import asyncio
from datetime import datetime

from aiofile import async_open as open
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, elevenlabs

import logging
from prompts import CHAT_INSTRUCTIONS, INITIAL_MESSAGE
from api import ClinicMateFunctions

logger = logging.getLogger("hospital-registration")
logger.setLevel(logging.INFO)

load_dotenv()

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
        
        # Check for registration confirmation in the message
        if fnc_ctx.patient_name and fnc_ctx.date_of_birth and not fnc_ctx.is_registered:
            if "registered" in msg.content.lower() and "successfully" in msg.content.lower():
                # Call the register function when the agent confirms registration
                asyncio.create_task(
                    fnc_ctx.register_patient(fnc_ctx.patient_name, fnc_ctx.date_of_birth)
                )

    # Set up file writing for conversation logs
    async def write_transcription():
        async with open("patient_registration.log", "w") as f:
            while True:
                msg = await log_queue.get()
                if msg is None:
                    break
                await f.write(msg)

    write_task = asyncio.create_task(write_transcription())

    async def finish_queue():
        log_queue.put_nowait(None)
        await write_task

    ctx.add_shutdown_callback(finish_queue)

    # Start the conversation with the initial greeting
    await agent.say(INITIAL_MESSAGE, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
