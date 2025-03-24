import asyncio
from datetime import datetime
from aiofile import async_open as open
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.rtc._proto.room_pb2 import ConnectionState
import logging
from prompts import CHAT_INSTRUCTIONS, INITIAL_MESSAGE
from api import ClinicMateFunctions
import call_processor
import database 
from typing import Dict, Any

logger = logging.getLogger("hospital-registration")
logger.setLevel(logging.INFO)

load_dotenv()

# Initialize database when the application starts
database.create_db_and_tables()
logger.info("Database initialized - tables created")

async def entrypoint(ctx: JobContext):
    """Main entry point for the hospital registration agent"""
    
    # Create our function context for patient registration
    fnc_ctx = ClinicMateFunctions()
    
    # Initialize chat context with system instructions
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=CHAT_INSTRUCTIONS
    )

    # Connect to the room and wait for a participant
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    
    # Create the voice pipeline agent
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=elevenlabs.TTS(),
        fnc_ctx=fnc_ctx,
        chat_ctx=initial_ctx,
    )
    
    # Start the assistant
    agent.start(ctx.room, participant)

    # Set up logging of the conversation
    log_queue = asyncio.Queue()
    # Flag to track if we've already processed end-of-call actions
    call_end_processed = False
    # Patient ID if we've registered the patient
    patient_id = None

    # Track conversation history to help extract patient information later
    conversation_history = []

    @agent.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        # Log user messages
        if isinstance(msg.content, list):
            content = "\n".join(
                "[image]" if isinstance(x, llm.ChatImage) else x for x in msg
            )
        else:
            content = msg.content
        
        log_queue.put_nowait(f"[{datetime.now()}] USER:\n{content}\n\n")
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": content})
        # Make conversation history accessible to function context
        fnc_ctx.conversation_history = conversation_history

    @agent.on("agent_speech_committed")
    def on_agent_speech_committed(msg: llm.ChatMessage):
        # Log agent messages
        content = msg.content
        log_queue.put_nowait(f"[{datetime.now()}] AGENT:\n{content}\n\n")
        
        # Add to conversation history
        conversation_history.append({"role": "assistant", "content": content})
        # Make conversation history accessible to function context
        fnc_ctx.conversation_history = conversation_history
    
    @agent.on("function_call_succeeded")
    def on_function_call_succeeded(
        func_name: str,
        func_args: Dict[str, Any],
        func_result: Any,
        ctx: ClinicMateFunctions,
    ):
        """Handle post-function call logic when a function succeeds (synchronous wrapper)."""
        nonlocal patient_id
        
        logger.info(f"Function {func_name} succeeded with result: {func_result}")
        
        # Log in a synchronous manner
        log_queue.put_nowait(f"[{datetime.now()}] FUNCTION CALL: {func_name}\nRESULT: {func_result}\n\n")
        
        # This is the async helper function that will be scheduled as a task
        async def handle_function_success():
            nonlocal patient_id
            
            # If this is a register_patient function call, let's capture the initial patient data
            if func_name == "register_patient":
                if "patient_name" in func_args and func_args["patient_name"]:
                    ctx.patient_name = func_args["patient_name"]
                    logger.info(f"Set patient name from register_patient: {ctx.patient_name}")
                    log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Captured patient name: {ctx.patient_name}\n\n")
                
                if func_args.get("date_of_birth"):
                    ctx.date_of_birth = func_args["date_of_birth"]
                    logger.info(f"Set patient DOB from register_patient: {ctx.date_of_birth}")
                    log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Captured DOB: {ctx.date_of_birth}\n\n")
            
            # If this is a confirm_information function, check if we have enough patient data
            # before trying to save the patient
            if func_name == "confirm_information" and func_args.get("confirmed"):
                logger.info("Patient information confirmed. Checking for complete data...")
                
                # Check if we have the minimum required fields
                have_name = bool(ctx.patient_name and ctx.patient_name.strip())
                have_dob = bool(ctx.date_of_birth and ctx.date_of_birth.strip())
                
                # If we're missing either name or DOB, try to extract them from conversation
                if not have_name or not have_dob:
                    logger.warning(f"Missing critical patient data: Name: {have_name}, DOB: {have_dob}")
                    
                    # Import the extraction function from call_processor
                    from call_processor import extract_data_from_conversation
                    
                    # Try to extract missing name from conversation
                    if not have_name and hasattr(ctx, 'conversation_history'):
                        extracted_name = extract_data_from_conversation(ctx.conversation_history, 'name')
                        if extracted_name:
                            ctx.patient_name = extracted_name
                            have_name = True
                            logger.info(f"Extracted patient name from conversation: {extracted_name}")
                            log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Extracted name from conversation: {extracted_name}\n\n")
                    
                    # Try to extract missing DOB from conversation
                    if not have_dob and hasattr(ctx, 'conversation_history'):
                        extracted_dob = extract_data_from_conversation(ctx.conversation_history, 'dob')
                        if extracted_dob:
                            ctx.date_of_birth = extracted_dob
                            have_dob = True
                            logger.info(f"Extracted patient DOB from conversation: {extracted_dob}")
                            log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Extracted DOB from conversation: {extracted_dob}\n\n")
                
                # If we have the minimum required fields, save the patient
                if have_name and have_dob:
                    try:
                        new_patient_id = await database.save_patient_from_context(ctx)
                        if new_patient_id:
                            patient_id = new_patient_id
                            ctx.database_patient_id = new_patient_id
                            logger.info(f"Registration completed for patient: {ctx.patient_name} (ID: {patient_id})")
                            log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Patient saved to database with ID {patient_id}\n\n")
                        else:
                            logger.warning(f"Registration failed for patient: {ctx.patient_name}")
                            log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Failed to save patient to database\n\n")
                    except Exception as e:
                        logger.error(f"Error saving patient: {str(e)}")
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Error saving patient: {str(e)}\n\n")
                else:
                    logger.warning(f"Cannot save patient to database: Missing name ({have_name}) or date of birth ({have_dob})")
                    log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Cannot save patient to database: Missing required information\n\n")
            
            # If specific information is collected, incrementally update existing patient record
            if patient_id and func_name in ("collect_insurance_info", "collect_medical_complaint", 
                                          "collect_address", "collect_phone", "collect_email"):
                try:
                    # Update the patient record with newly collected information
                    success = await database.update_patient_from_context(patient_id, ctx, func_name)
                    if success:
                        logger.info(f"Updated patient record with {func_name} information")
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Updated patient record with {func_name} information\n\n")
                    else:
                        logger.warning(f"Failed to update patient record for {func_name}")
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Failed to update patient record with {func_name} information\n\n")
                except Exception as e:
                    logger.error(f"Error updating patient record: {str(e)}")
                    log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Error updating patient record: {str(e)}\n\n")
            
            # Store the appointment ID if booking was successful
            if func_name == "book_appointment" and ctx.appointment_details and ctx.appointment_id:
                logger.info(f"Stored appointment ID: {ctx.appointment_id}")
                log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Stored appointment ID: {ctx.appointment_id}\n\n")

        # Create a task to execute the async function
        asyncio.create_task(handle_function_success())

    async def process_end_of_call():
        """Process end-of-call tasks like saving data and generating summaries"""
        nonlocal call_end_processed
        nonlocal patient_id
        
        # Only process once
        if call_end_processed:
            return
            
        call_end_processed = True
        logger.info("Processing end of call tasks")
        
        # Use the call_processor module function to handle end of call processing
        updated_patient_id, call_summary, success = await call_processor.process_call_end_from_context(
            fnc_ctx, 
            patient_id=patient_id, 
            log_queue=log_queue
        )
        
        # Update patient_id if it was created during end of call processing
        if updated_patient_id and not patient_id:
            patient_id = updated_patient_id

    # Use shutdown callback as a reliable method for detecting call end
    async def finish_queue():
        """Final cleanup when the job is shutting down"""
        logger.info("Job shutdown callback triggered - ensuring call end processing")
        # Ensure end-of-call processing happens
        await process_end_of_call()
        
        # Signal the write task to finish
        log_queue.put_nowait(None)
        await write_task

    ctx.add_shutdown_callback(finish_queue)
    
    # Set up file writing for conversation logs
    async def write_transcription():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"patient_registration_{timestamp}.log"
        async with open(filename, "w") as f:
            while True:
                msg = await log_queue.get()
                if msg is None:
                    break
                await f.write(msg)

    write_task = asyncio.create_task(write_transcription())

    # Start the conversation with the initial greeting
    await agent.say(INITIAL_MESSAGE, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
