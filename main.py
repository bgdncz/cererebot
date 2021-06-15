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

TOKEN = ''

START_MSG = 'Bună\! Hai să creem cererea/plângerea/scrisoarea ta nouă\. Poți să anulezi oricând procesul prin comanda /anulare\.'
ADDRESS_MSG = 'În primul rând, am nevoie de adresa persoanei/instituției căreia te adresezi\. Aceasta apare în partea de dreapta sus\.'
TO_MSG = 'Mulțumesc\! Cui îi este adresată scrisoarea ta? De exemplu: Domnului Primar'
CONTENT_MSG = 'OK\! Care este conținutul scrisorii tale?\nCând scrii ceva, ai posibilitatea să formatezi textul în *bold*, _italic_, __underline__ sau să adaugi un link prin interfața Telegram; eu le înțeleg pe toate\.'
END_MSG = 'Cererea/plângerea ta e gata 🎉\nDacă vrei să o semnezi electronic, o poți face pe [MSign](https://msign.gov.md/#/sign/upload)\.\nDacă vrei să mai creezi un document, dă /start\.'
CANCEL_MSG = 'Ok, poate data viitoare\. Poți să începi o scrisoare nouă prin /start\.'
SIGN_STAMP_MSG = 'Vrei să pui o semnătură sau ștampilă pe scrisoare?'
SIGN_STAMP_KEYBOARD = [['Semnătură', 'Ștampilă', 'Nu']]
SIGN_MSG = 'Trimite o imagine sau un fișier JPEG/PNG care conține ștampila/semnătura ta:'
ERR_MSG = 'Ceva nu a mers bine\. Încearcă să creezi o cerere din nou prin comanda /start\. \(Poți să faci forward la mesaje ca să nu te complici\)'
ABOUT_MSG = 'Acest bot a fost creat de @boghison\. Codul este disponibil [aici](https://github.com/boghison/cererebot)\.'

PAR_INDENT = '<font color="#ffffff">aaaaaa</font>'

ADDRESS, TO, CONTENT, SIGN, SIGN2 = range(5)

TEMPLATE = """
<br>
<p align="right">{address}</p>
<br><br>
<p align="center">{to}</p>
<br>
<p>{content}</p>
<br>
<br>
<br>

<center>{date}                                                              {name}</center>
<br>
"""

class MyFPDF(FPDF, HTMLMixin):
    def create(self, data):
        self.set_doc_option('core_fonts_encoding', 'utf-8')
        self.add_font('Merriweather', '', 'merriweather.ttf', uni=True)
        self.add_font('Merriweather', 'B', 'merriweatherB.ttf', uni=True)
        self.add_font('Merriweather', 'I', 'merriweatherI.ttf', uni=True)
        self.set_font('Merriweather', '', 12)
        self.add_page()
        self.set_margin(25)
        self.write_html(TEMPLATE.format(**data))

    def stamp(self, img_url, height):
        self.image(img_url, x=130, h=height)

        

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

def sign(update: Update, ctx: CallbackContext) -> int:
    msg = update.message.text
    if msg == 'Semnătură':
        ctx.user_data["img_height"] = 15 # mm
    elif msg == "Ștampilă":
        ctx.user_data["img_height"] = 35 # mm
    else:
        pdf = MyFPDF()
        pdf.create(ctx.user_data)
        update.message.reply_document(bytes(pdf.output()), filename="document.pdf", caption=END_MSG, parse_mode=constants.PARSEMODE_MARKDOWN_V2, reply_markup=ReplyKeyboardRemove())
        del pdf
        ctx.user_data.clear()
        return ConversationHandler.END

    update.message.reply_markdown_v2(SIGN_MSG, reply_markup=ReplyKeyboardRemove())
    return SIGN2

def sign2(update: Update, ctx: CallbackContext) -> int:
    img_url = ""
    if update.message.document:
        img_url = update.message.document.get_file().file_path
    else:
        img_url = update.message.photo[-1].get_file().file_path
    
    pdf = MyFPDF()
    height = ctx.user_data["img_height"]
    del ctx.user_data["img_height"]
    pdf.create(ctx.user_data)
    pdf.stamp(img_url, height)

    update.message.reply_document(bytes(pdf.output()), filename="document.pdf", caption=END_MSG, parse_mode=constants.PARSEMODE_MARKDOWN_V2)
    del pdf
    ctx.user_data.clear()
    return ConversationHandler.END

def content(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["content"] = PAR_INDENT + update.message.text_html_urled.replace('\n', '<br>' + PAR_INDENT)

    update.message.reply_markdown_v2(SIGN_STAMP_MSG, reply_markup=ReplyKeyboardMarkup(SIGN_STAMP_KEYBOARD, one_time_keyboard=True))
    return SIGN

def cancel(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data.clear()
    update.message.reply_markdown_v2(CANCEL_MSG)

    return ConversationHandler.END

def about(update: Update, _: CallbackContext) -> None:
    update.message.reply_markdown_v2(ABOUT_MSG)


def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, address)],
            TO: [MessageHandler(Filters.text & ~Filters.command, to)],
            CONTENT: [MessageHandler(Filters.text & ~Filters.command, content)],
            SIGN: [MessageHandler(Filters.text & ~Filters.command, sign)],
            SIGN2: [MessageHandler(Filters.document.file_extension("png") | Filters.document.file_extension("jpg") | Filters.photo & ~Filters.command, sign2)],
        },
        fallbacks=[CommandHandler('anulare', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("about", about))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
