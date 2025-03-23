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

    @agent.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        # Log user messages
        if isinstance(msg.content, list):
            msg.content = "\n".join(
                "[image]" if isinstance(x, llm.ChatImage) else x for x in msg
            )
        log_queue.put_nowait(f"[{datetime.now()}] USER:\n{msg.content}\n\n")

    @agent.on("agent_speech_committed")
    def on_agent_speech_committed(msg: llm.ChatMessage):
        # Log agent messages
        log_queue.put_nowait(f"[{datetime.now()}] AGENT:\n{msg.content}\n\n")
    
    @agent.on("function_call_succeeded")
    def on_function_call_succeeded(name: str, result: str):
        """
        Handle successful function calls to incrementally save patient information
        to the database as it is collected during the call
        """
        # Create an async task to handle the database operations
        asyncio.create_task(handle_function_success(name, result))
        
        # Log in a synchronous manner
        log_queue.put_nowait(f"[{datetime.now()}] FUNCTION CALL: {name}\nRESULT: {result}\n\n")
    
    async def handle_function_success(name: str, result: str):
        """Async handler for function call success"""
        nonlocal patient_id
        
        # If we've confirmed the patient information, save to the database
        if name == "confirm_information" and fnc_ctx.is_registered:
            # Only save if we haven't already saved the patient
            if patient_id is None:
                try:
                    # Try to save the patient to the database using the database module function
                    patient_id = await database.save_patient_from_context(fnc_ctx)
                    if patient_id:
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Patient saved to database with ID {patient_id}\n\n")
                except Exception as e:
                    logger.error(f"Error saving patient to database: {str(e)}")
        
        # If specific information is collected, incrementally update existing patient record
        if patient_id and name in ("collect_insurance_info", "collect_medical_complaint", 
                               "collect_address", "collect_phone", "collect_email"):
            try:
                # Update the patient record with newly collected information using the database module function
                success = await database.update_patient_from_context(patient_id, fnc_ctx, name)
                if not success:
                    logger.warning(f"Failed to update patient record for {name}")
            except Exception as e:
                logger.error(f"Error updating patient record: {str(e)}")

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
