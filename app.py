import streamlit as st
import pandas as pd
import re
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication


st.set_page_config(layout="wide")

dict_matiere = {
    'C': 'Chimie',
    'S': 'SI',
    'M': 'Mathématiques',
    'D': 'Allemand',
    'F': 'Français',
    'A': 'Anglais',
    'P': 'Physique'
}


def send_email(sender, password, receiver, others, smtp_server, smtp_port, email_message, subject, attachment=None):
    message = MIMEMultipart()
    message['To'] = Header(receiver)
    message['From']  = Header(sender)
    message['CC'] = Header(others)
    message['Subject'] = Header(subject)
    message.attach(MIMEText(email_message,'plain', 'utf-8'))
    if attachment:
        att = MIMEApplication(attachment.read(), _subtype="txt")
        att.add_header('Content-Disposition', 'attachment', filename=attachment.name)
        message.attach(att)
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.ehlo()
    server.login(sender, password)
    text = message.as_string()
    server.sendmail(sender, receiver, text)
    server.quit()


def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="500" height="600" type="application/pdf"></iframe>'
    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


def send_to_mails(index, dict_slots, df_groupes, df_mails):
    group = dict_slots[index]['Groupes']
    names = [el.lower() for el in list(df_groupes.iloc[int(group) - 1].dropna()[1:])]
    df_names = df_mails[df_mails['Eleve'].isin(names)]
    lst_mails = list(df_names['Mail'])
    st.info("Eleves: {}".format(" - ".join(names)))
    
    if '-' in dict_slots[index]['Creneau']:
        creneau = st.selectbox('Choisissez le créneau: ', dict_slots[index]['Creneau'].split('-'))
    else:
        creneau = dict_slots[index]['Creneau']
    day, hour = creneau.split(' ')

    if '-' in dict_slots[index]['Salle']:
        salle = st.selectbox('Choisissez la salle: ', dict_slots[index]['Salle'].split('-'), key=index)
    else:
        salle = dict_slots[index]['Salle']
    salle = re.sub("\(.*\)", "", salle)
    
    str_mail_def = str_mail.format(
        len(names),
        dict_slots[index]['Professeur'],
        dict_matiere[dict_slots[index]['Matière'][0]],
        day,
        hour,
        salle,
        dict_slots[index]['Professeur'],
        dict_slots[index]['Mail']
    )
    SUBJECT = 'Colles {}: {} {}'.format(
        dict_matiere[dict_slots[index]['Matière'][0]],
        day,
        hour
    )
    TEXT = st.text_area('Mail: ', str_mail_def, height=400)

    if dict_slots[index]['Professeur'] == "Mr Monnier":
        send = st.button("Envoyer le mail: ", key="send{}".format(index))
        if send:
            send_email(st.secrets['USERMAIL'], st.secrets['USERPASSWORD'], ",".join(lst_mails), "pcsiahoche@yahoo.fr", st.secrets["SMTP_SERVER"], st.secrets["SMTP_PORT"], TEXT, SUBJECT)
            st.success('Envoyé!')


if __name__ == "__main__":
    st.title('Colles 2022 / 2023: Mathématiques PCSIA Hoche')
    st.markdown("Ce site web permet d'envoyer automatiquement des mails aux élèves des colles.")

    password = st.text_input('Entrez le mot de passe:', '')

    if password == st.secrets['PASSWORD']:
        df_colleurs = pd.read_csv('colleurs.csv')
        df_colloscope = pd.read_csv('colloscope.csv')
        df_groupes = pd.read_csv('groupes.csv')
        df_mails = pd.read_csv('mails.csv')

        col_1, col_2 = st.columns(2)

        with col_1:
            st.session_state.week = st.selectbox("Semaine du: ", list(df_colloscope['Semaine']))
        
        with col_2:
            st.session_state.teacher = st.selectbox("Professeur: ", list(set(df_colleurs['Professeur'])))
        
        s_colles = df_colloscope.loc[df_colloscope['Semaine'] == st.session_state.week].iloc[0]
        df_slots = df_colleurs.loc[df_colleurs['Professeur'] == st.session_state.teacher]

        groups = []
        for slot in list(df_slots['Matière']):
            s_colles_grp = s_colles.str.contains(slot)
            try:
                grp = list(s_colles_grp[s_colles_grp].index)[0]
            except:
                grp = None
            groups.append(grp)

        df_slots.insert(1, "Groupes", groups)
        dict_slots = df_slots.to_dict('record')

        with open('mail.txt', 'r') as f:
            str_mail = "".join(f.readlines())
            f.close()

        if len(dict_slots) == 1:
            send_to_mails(0, dict_slots, df_groupes, df_mails)

        elif len(df_slots) == 2:
            with col_1:
                send_to_mails(0, dict_slots, df_groupes, df_mails)

            with col_2:
                send_to_mails(1, dict_slots, df_groupes, df_mails)

        else:
            pass
