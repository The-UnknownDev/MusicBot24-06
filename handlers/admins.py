# Copyright (C) 2021 VeezMusicProject

from asyncio import QueueEmpty

from callsmusic import callsmusic
from callsmusic.queues import queues
from config import BOT_USERNAME, que
from cache.admins import admins
from helpers.channelmusic import get_chat_id
from helpers.dbtools import delcmd_is_on, delcmd_off, delcmd_on, handle_user_status
from helpers.decorators import authorized_users_only, errors
from helpers.filters import command, other_filters
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

ACTV_CALLS = []

@Client.on_message()
async def _(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)


# Back Button
BACK_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔙 Go Back", callback_data="cbback")]]
)

# @Client.on_message(filters.text & ~filters.private)
# async def delcmd(_, message: Message):
#    if await delcmd_is_on(message.chat.id) and message.text.startswith("/") or message.text.startswith("!") or message.text.startswith("."):
#        await message.delete()
#    await message.continue_propagation()

# remove the ( # ) if you want the auto del cmd feature is on


@Client.on_message(command(["reload", f"reload@{BOT_USERNAME}"]) & other_filters)
async def update_admin(client, message):
    global admins
    new_admins = []
    new_ads = await client.get_chat_members(message.chat.id, filter="administrators")
    for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text(
        "✅ Bot **Reloaded Correctly !**\n✅ **Admin List** Has Been **Updated !** Support Group - @ByteBotsSupport "
    )


# Control Menu Of Player
@Client.on_message(command(["control", f"control@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def controlset(_, message: Message):
    await message.reply_text(
        "💡 **Here Is The Control Menu Of Bot :**",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏸ Pause", callback_data="cbpause"),
                    InlineKeyboardButton("▶️ Resume", callback_data="cbresume"),
                ],
                [
                    InlineKeyboardButton("⏩ Skip", callback_data="cbskip"),
                    InlineKeyboardButton("⏹ Stop", callback_data="cbend"),
                ],
                [InlineKeyboardButton("⛔ Anti Cmd", callback_data="cbdelcmds")],
                [InlineKeyboardButton("🗑 Close", callback_data="close")],
            ]
        ),
    )


@Client.on_message(command(["pause", f"pause@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def pause(_, message: Message):
    chat_id = get_chat_id(message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("❌ **No Music Is Currently Playing** Support - @ByteBotsSupport")
    else:
        await callsmusic.pytgcalls.pause_stream(chat_id)
        await message.reply_text(
            "⏸ **Track paused.**\n\n• **To Resume The Playback, Use The**\n» /resume Command."
        )


@Client.on_message(command(["resume", f"resume@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def resume(_, message: Message):
    chat_id = get_chat_id(message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("❌ **No Music Is Paused** Chatting Group - @Friendship_Junction")
    else:
        await callsmusic.pytgcalls.resume_stream(chat_id)
        await message.reply_text(
            "▶️ **Track resumed.**\n\n• **To Pause The Playback, Use The**\n» /pause Command. Thanks- @Arpit_Chaurasiya"
        )


@Client.on_message(command(["end", f"end@{BOT_USERNAME}", "stop", f"end@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    chat_id = get_chat_id(message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("❌ **No Music Is Currently Playing**")
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass
        await callsmusic.pytgcalls.leave_group_call(chat_id)
        await message.reply_text("✅ **Music Playback Has Ended**")


@Client.on_message(command(["skip", f"skip@{BOT_USERNAME}", "next", f"next@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def skip(_, message: Message):
    global que
    chat_id = message.chat.id
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("❌ **No Music Is Currently Playing**")
    else:
        queues.task_done(chat_id)
        
        if queues.is_empty(chat_id):
            await callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            await callsmusic.pytgcalls.change_stream(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        callsmusic.queues.get(chat_id)["file"],
                    ),
                ),
            )
                
    qeue = que.get(chat_id)
    if qeue:
        qeue.pop(0)
    if not qeue:
        return
    await message.reply_text("⏭ **You've Skipped To The Next Song. Join - @Arpit_Chaurasiya**")


@Client.on_message(command(["auth", f"auth@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def authenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("💡 reply to message to authorize user !")
    if message.reply_to_message.from_user.id not in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.append(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🟢 User Authorized.\n\nFrom Now On, That's User Can Use The Admin Commands."
        )
    else:
        await message.reply("✅ User Already Authorized!")


@Client.on_message(command(["unauth", f"deauth@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def deautenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("💡 Reply To Message To Deauthorize User !")
    if message.reply_to_message.from_user.id in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.remove(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🔴 User Deauthorized.\n\nFrom Now On, That's User Can't Use The Admin Commands."
        )
    else:
        await message.reply("✅ User Already Deauthorized!")


# this is a anti cmd feature
@Client.on_message(command(["delcmd", f"delcmd@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def delcmdc(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Read The /help Message To Know How To Use This Command"
        )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "on":
        if await delcmd_is_on(message.chat.id):
            return await message.reply_text("✅ Already Activated")
        await delcmd_on(chat_id)
        await message.reply_text("🟢 Activated Successfully")
    elif status == "off":
        await delcmd_off(chat_id)
        await message.reply_text("🔴 Disabled Successfully")
    else:
        await message.reply_text(
            "Read The /help Message To Know How To Use This Command"
        )


# music player callbacks (control by buttons feature)


@Client.on_callback_query(filters.regex("cbpause"))
async def cbpause(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Only Admin Can Tap This Button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await query.edit_message_text(
            "❌ **No Music Is Currently Playing**", reply_markup=BACK_BUTTON
        )
    else:
        await callsmusic.pytgcalls.pause_stream(chat_id)
        await query.edit_message_text(
            "⏸ Music Playback Has Been Paused", reply_markup=BACK_BUTTON
        )


@Client.on_callback_query(filters.regex("cbresume"))
async def cbresume(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Only Admin Can Tap This Button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await query.edit_message_text(
            "❌ **No Music Is Paused**", reply_markup=BACK_BUTTON
        )
    else:
        await callsmusic.pytgcalls.resume_stream(chat_id)
        await query.edit_message_text(
            "▶️ Music Playback Has Been Resumed", reply_markup=BACK_BUTTON
        )


@Client.on_callback_query(filters.regex("cbend"))
async def cbend(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Only Admin Can Tap This Button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await query.edit_message_text(
            "❌ **No Music Is Currently Playing**", reply_markup=BACK_BUTTON
        )
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass
        
        await callsmusic.pytgcalls.leave_group_call(chat_id)
        await query.edit_message_text(
            "✅ The Music Queue Has Been Cleared And Successfully Left Voice Chat",
            reply_markup=BACK_BUTTON,
        )


@Client.on_callback_query(filters.regex("cbskip"))
async def cbskip(_, query: CallbackQuery):
    global que
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 Only Admin Can Tap This Button !", show_alert=True)
    chat_id = get_chat_id(query.message.chat)
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await query.edit_message_text(
            "❌ **No Music Is Currently Playing**", reply_markup=BACK_BUTTON
        )
    else:
        queues.task_done(chat_id)
        
        if queues.is_empty(chat_id):
            await callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            await callsmusic.pytgcalls.change_stream(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        queues.get(query.message.chat.id)["file"],
                    ),
                ),
            )

    qeue = que.get(chat_id)
    if qeue:
        qeue.pop(0)
    if not qeue:
        return
    await query.edit_message_text(
        "⏭ **You've Skipped To The Next Song**", reply_markup=BACK_BUTTON
    )


@Client.on_message(command(["volume", f"volume@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def change_volume(client, message):
    range = message.command[1]
    chat_id = message.chat.id
    try:
       await callsmusic.pytgcalls.change_volume_call(chat_id, volume=int(range))
       await message.reply(f"✅ **Volume Set To:** ```{range}%```")
    except Exception as e:
       await message.reply(f"**error:** {e}")
