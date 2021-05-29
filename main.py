from fpdf import FPDF, HTMLMixin
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, constants
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from datetime import date
import locale

# set locale 

locale.setlocale(locale.LC_TIME, 'ro_RO')

def today():
    return date.today().strftime("%d %B %Y").lower()

# constants

TOKEN = 'TOKEN'

START_MSG = 'Bună\! Hai să creem cererea/plângerea/scrisoarea ta nouă\. Poți să anulezi oricând procesul prin comanda /anulare\.'
ADDRESS_MSG = 'În primul rând, am nevoie de adresa persoanei/instituției căreia te adresezi\. Aceasta apare în partea de dreapta sus\.'
TO_MSG = 'Mulțumesc\! Cui îi este adresată scrisoarea ta? De exemplu: Domnului Primar'
CONTENT_MSG = 'OK\! Care este conținutul scrisorii tale?\nCând scrii ceva, ai posibilitatea să formatezi textul în *bold*, _italic_, __underline__ sau să adaugi un link prin interfața Telegram; eu le înțeleg pe toate\.'
END_MSG = 'Cererea/plângerea ta e gata 🎉\nDacă vrei să o semnezi, o poți face pe [MSign](https://msign.gov.md/#/sign/upload)\.\nDacă vrei să mai creezi un document, dă /start\.'
CANCEL_MSG = 'Ok, poate data viitoare\. Poți să începi o scrisoare nouă prin /start\.'

PAR_INDENT = '<font color="#ffffff">aaaaaa</font>'

ADDRESS, TO, CONTENT = range(3)

TEMPLATE = """
<br><br><br>
<p align="right">{address}</p>
<br><br>
<p align="center">{to}</p>
<br>
<p>{content}</p>
<br>
<br>
<br>

<center>{date}                                                              {name}</center>
"""

class MyFPDF(FPDF, HTMLMixin):
    pass
        

def start(update: Update, ctx: CallbackContext) -> int:
    update.message.reply_markdown_v2(START_MSG)
    update.message.reply_markdown_v2(ADDRESS_MSG)
    
    ctx.user_data["date"] = today()
    ctx.user_data["name"] = update.message.from_user.first_name + ' ' + str(update.message.from_user.last_name or '')

    return ADDRESS


def address(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["address"] = update.message.text.replace('\n', '<br>') # switch to urled when possible
    update.message.reply_markdown_v2(TO_MSG)

    return TO


def to(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["to"] = update.message.text + ','

    update.message.reply_markdown_v2(CONTENT_MSG)
    return CONTENT

def content(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["content"] = PAR_INDENT + update.message.text_html_urled.replace('\n', '<br>' + PAR_INDENT)

    mine = TEMPLATE.format(**ctx.user_data)

    pdf = MyFPDF()

    pdf.set_doc_option('core_fonts_encoding', 'utf-8')
    pdf.add_font('Merriweather', '', 'merriweather.ttf', uni=True)
    pdf.add_font('Merriweather', 'B', 'merriweatherB.ttf', uni=True)
    pdf.add_font('Merriweather', 'I', 'merriweatherI.ttf', uni=True)
    pdf.set_font('Merriweather', '', 14)
    

    pdf.add_page()
    pdf.set_margin(25)
    pdf.write_html(TEMPLATE.format(**ctx.user_data))
    update.message.reply_document(bytes(pdf.output()), filename="document.pdf", caption=END_MSG, parse_mode=constants.PARSEMODE_MARKDOWN_V2)

    return ConversationHandler.END


def cancel(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data.clear()
    update.message.reply_markdown_v2(CANCEL_MSG)

    return ConversationHandler.END


def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, address)],
            TO: [MessageHandler(Filters.text & ~Filters.command, to)],
            CONTENT: [MessageHandler(Filters.text & ~Filters.command, content)],
        },
        fallbacks=[CommandHandler('anulare', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
