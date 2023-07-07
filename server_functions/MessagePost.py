from data.channel_class import Channel
from data.message_class import Message
from data.reply_markup_class import Keyboard
from data.user_class import User
from aiogram.utils.markdown import hlink
from aiogram import types, Bot
from ast import literal_eval

actions = {'reply': None, 'pin': None, 'share': None, 'restrict_comms': None}
async def post_media_group(row, db_sess, bot: Bot, channel_id=None):
    global actions
    media_group = types.MediaGroup()
    media_group_parts = db_sess.query(Message).filter(Message.mediagroup_id == row,
                                                      Message.type_media != 'caption').all()
    caption = db_sess.query(Message).filter(Message.mediagroup_id == row, Message.type_media == 'caption').first()
    if caption.reply_post:
        actions['reply'] = caption.reply_post
    if caption:
        caption = str(caption.tg_id)
    for i in media_group_parts:
        media_group.attach({"media": i.tg_id, "type": i.type_media, "caption": caption})
        caption = None
    if not channel_id:
        channel_id = db_sess.query(Channel).filter(media_group_parts[0].channel_id == Channel.id).first().tg_id
    await bot.send_media_group(media=media_group, chat_id=channel_id, reply_to_message_id=actions['reply'])
    actions = {'reply': None, 'pin': None, 'share': None, 'restrict_comms': None}
hidden_messages = []
urlbuttons = []
async def post_message(row, db_sess, bot: Bot, channel_id=None):
    global actions
    result_markup = types.InlineKeyboardMarkup()
    if row.reply_markup:
        mrkp = db_sess.query(Keyboard).filter(row.tg_id == Keyboard.markup_id).all()
        hidden_content_c = 0

        for x in range(len(mrkp)):
            i = mrkp[x]
            if i.content_text:
                button = types.InlineKeyboardButton(text=i.content_text, callback_data='hidden_'+row.tg_id+'_'+str(hidden_content_c))
                hidden_messages.append(button)
                #result_markup.add(button)
                hidden_content_c+=1
            # elif i.content_url_text:
            #     editmsg.append(i.content_url_text)
            #     editmsg.append(i.type_of_string)
            else:
                i = literal_eval(i.content)
                #print(i)
                # if type(i) == tuple:
                #     #print(i)
                #     urlbuttons.append(*i)
                #     #result_markup.add(*i)
                # else:
                urlbuttons.append(i)
                    #esult_markup.add(i)
    if row.reply_post:
        actions['reply'] = row.reply_post

    for i in hidden_messages:
        result_markup.add(i)
    for i in urlbuttons:
        if type(i) == tuple:
            result_markup.add(*i)
        else:
            result_markup.add(i)
    sender_id = db_sess.query(User).filter(row.sender_id == User.id).first().tg_id
    if not channel_id:
        channel_id = db_sess.query(Channel).filter(row.channel_id == Channel.id).first().tg_id

    msg_copy = await bot.copy_message(chat_id=channel_id, from_chat_id=sender_id, message_id=row.tg_id,
                                      reply_markup=result_markup, reply_to_message_id=actions['reply'])
    actions = {'reply': None, 'pin': None, 'share': None, 'restrict_comms': None}
    # if editmsg and editmsg[1] == 'text':
    #    await bot.edit_message_text(message_id=msg_copy.message_id, chat_id=channel_id, text=editmsg[0],
    #                                parse_mode='HTML',
    #                                reply_markup=result_markup)
    # elif editmsg and editmsg[1] == 'caption':
    #     await bot.edit_message_caption(message_id=msg_copy.message_id, chat_id=channel_id, caption=editmsg[0],
    #                                    parse_mode='HTML',
    #                                    reply_markup=result_markup)
#    db_sess.query(Message).filter(Message.tg_id == row.tg_id).update({'id_on_post ': msg_copy.message_id})
