import asyncio
import os
import json
from datetime import datetime

from livekit import rtc
from livekit.agents import (
    JobContext, 
    WorkerOptions, 
    cli, 
    JobProcess
)
from livekit.agents.llm import (
    ChatContext,
    ChatMessage,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.log import logger
from livekit.plugins import deepgram, silero, cartesia, openai
from typing import Dict, Any
from prompts import CHAT_MSG_INSTRUCTIONS
from dotenv import load_dotenv

load_dotenv()


def prewarm(proc: JobProcess):
    # preload models when process starts to speed up first interaction
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Create a system prompt that guides the assistant to collect name and phone number
    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=CHAT_MSG_INSTRUCTIONS
            )
        ]
    )

    # Create a dictionary to store collected information
    user_info: Dict[str, Any] = {
        "name": None,
        "phone": None,
        "timestamp": None
    }

    # Create the voice pipeline agent with fixed voice settings
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-2"),  # Fixed voice model
        chat_ctx=initial_ctx,
    )

    is_user_speaking = False
    is_agent_speaking = False

    # Connect event handlers for speaking states
    @agent.on("agent_started_speaking")
    def agent_started_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = True

    @agent.on("agent_stopped_speaking")
    def agent_stopped_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = False

    @agent.on("user_started_speaking")
    def user_started_speaking():
        nonlocal is_user_speaking
        is_user_speaking = True

    @agent.on("user_stopped_speaking")
    def user_stopped_speaking():
        nonlocal is_user_speaking
        is_user_speaking = False

    # Set up a message handler to extract and log information
    @agent.on("message_received")
    def on_message_received(message: ChatMessage):
        if message.role != "assistant":
            return
        
        # Check if we need to update user info based on conversation context
        # This is a simple implementation and might need more sophisticated NLP in a real application
        if user_info["name"] is None and "name" in agent.chat_ctx.messages[-2].content.lower():
            # Extract potential name from the user's last message
            user_info["name"] = agent.chat_ctx.messages[-2].content
            logger.info(f"Collected name: {user_info['name']}")
        
        elif user_info["name"] is not None and user_info["phone"] is None and "phone" in agent.chat_ctx.messages[-2].content.lower():
            # Extract potential phone number from the user's last message
            user_info["phone"] = agent.chat_ctx.messages[-2].content
            user_info["timestamp"] = datetime.now().isoformat()
            logger.info(f"Collected phone: {user_info['phone']}")
            
            # Log the complete information once we have both
            if user_info["name"] and user_info["phone"]:
                log_user_information(user_info)

    await ctx.connect()
    
    # Start the agent and begin the conversation
    agent.start(ctx.room)
    await agent.say("Hello! I'm calling to collect some information. Could you please tell me your name?", allow_interruptions=True)


def log_user_information(user_info: Dict[str, Any]):
    """Log the collected user information to a file."""
    log_dir = "user_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"user_info_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Read existing logs if file exists
    existing_logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
    
    # Append new log
    existing_logs.append(user_info)
    
    # Write updated logs
    with open(log_file, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.info(f"User information logged successfully: {user_info['name']}, {user_info['phone']}")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))