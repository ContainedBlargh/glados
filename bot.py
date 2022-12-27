import discord
import os
from dotenv import load_dotenv
from assistant import setup, shutdown, stall, query, greeting, dead_air, ready
from glados import tts
from asyncio import sleep
# import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech import SpeechClient, RecognitionAudio, RecognitionConfig

load_dotenv()
bot = discord.Bot()
connections = {}
client = SpeechClient()
reset_next = True

@bot.event
async def on_ready():
    for client in bot.voice_clients:
        client.disconnect()

    await bot.change_presence(status=discord.Status.offline)
    print("waking up GLaDOS...")
    setup()
    print("GLaDOS is ready.")
    await bot.change_presence(status=discord.Status.online)


@bot.slash_command(name = "join", description = "Ask GLaDOS to join the conversation.")
async def join(ctx: discord.context.ApplicationContext):
    voice = ctx.author.voice
    if not voice:
        await ctx.respond("You are not in a voice channel!")
    
    vc = await voice.channel.connect()
    
    if ctx.guild_id in connections.keys():
        await ctx.respond("One at a time, please.")

    connections.update({ctx.guild_id: vc})
    vc.play(greeting())

    while vc.is_playing():
        await sleep(1)

    await ctx.respond("Ready.")


async def once_done(sink: discord.sinks.WaveSink, author: discord.Member, guild_id, *args):
    global reset_next
    print("RECORDING DONE")
    if guild_id not in connections.keys():
        return
    vc: discord.VoiceClient = connections[guild_id]
    try:
        vc.voice_connect()
    except:
        pass
    recorded_users = [(user_id, audio) for user_id, audio in sink.audio_data.items() if user_id == author.id]
    if len(recorded_users) != 1:
        return

    vc.play(stall())

    (user_id, audio) = recorded_users[0]
    audio: discord.sinks.core.AudioData = audio
    audio_bytes = audio.file.read()

    print("ATTEMPTING TO RECOGNIZE SPEECH")
    audio: RecognitionAudio = RecognitionAudio(content=audio_bytes)

    config = RecognitionConfig(
        sample_rate_hertz=48000,
        audio_channel_count=2,
        language_code="en-US",
        enable_separate_recognition_per_channel=False
    )
    response = client.recognize(config=config, audio=audio)
    question_text: str = '. '.join([result.alternatives[0].transcript for result in response.results])
    
    while vc.is_playing():
        await sleep(0.2)
        
    print(f"QUESTION: {question_text}")

    if question_text is None or question_text.strip() == "":
        print("DEAD AIR")
        vc.play(dead_air())
    else:
        print("QUERYING CHATGPT")
        answer = query(question_text, reset=reset_next)
        print(f"ANSWER: {answer}")
        vc.play(tts(answer))
        reset_next = False
    
    while vc.is_playing():
        await sleep(0.2)

    pass

@bot.slash_command(name="question", description = "Ask GLaDOS a question.")
async def question(ctx: discord.context.ApplicationContext, listen_seconds: discord.Option(int)):
    voice = ctx.author.voice
    if not voice:
        await ctx.respond("You are not in a voice channel!")
    if ctx.guild_id in connections.keys():
        vc: discord.VoiceClient = connections[ctx.guild_id]
        try:
            ctx.respond("Listening...")
        except discord.ApplicationCommandInvokeError as e:
            print(e)
        
        vc.play(ready())
        while vc.is_playing():
            await sleep(0.2)
        vc.start_recording(
            discord.sinks.WaveSink(),
            once_done,
            ctx.author,
            ctx.guild_id
        )
        await sleep(int(min(listen_seconds, 6)))
        vc.stop_recording()

@bot.slash_command(name="leave", description="Make GLaDOS leave the converation.")
async def leave(ctx: discord.context.ApplicationContext):
    global reset_next
    reset_next = True
    voice = ctx.author.voice
    if not voice:
        await ctx.respond("You are not in a voice channel!")
    
    if ctx.guild_id in connections.keys():
        vc: discord.VoiceClient = connections[ctx.guild_id]
        if vc.recording:
            vc.stop_recording()
        else:
            vc.stop()
        await vc.disconnect()
        await ctx.respond("GLaDOS has left the channel.")
    else:
        await ctx.respond("Can't leave a channel that GLaDOS is not currently in.")

bot.run(os.getenv('token'))