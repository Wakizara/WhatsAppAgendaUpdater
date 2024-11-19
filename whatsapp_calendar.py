from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import re
import os.path
import pickle

class WhatsAppCalendarBot:
    def __init__(self):
        # Configuration de Selenium pour WhatsApp Web
        self.driver = webdriver.Chrome()
        self.driver.get("https://web.whatsapp.com")
        
        # Attendre que l'utilisateur scanne le QR code
        input("Scannez le QR code et appuyez sur Entrée...")
        
        # Configuration Google Calendar
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def extract_date_time(self, message):
        # Exemple de patterns à détecter (à adapter selon vos besoins)
        patterns = [
            r'rendez-vous le (\d{1,2}/\d{1,2}/\d{4}) à (\d{1,2}h\d{2})',
            r'rdv (\d{1,2}/\d{1,2}) (?:à|a) (\d{1,2}[h:]?\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                date_str, time_str = match.groups()
                # Conversion en objet datetime
                try:
                    if '/' in date_str:
                        if len(date_str.split('/')) == 2:
                            date_str += f"/{datetime.now().year}"
                        date = datetime.strptime(date_str, "%d/%m/%Y")
                    time = datetime.strptime(time_str.replace('h', ':'), "%H:%M")
                    return datetime.combine(date.date(), time.time())
                except ValueError:
                    return None
        return None

    def create_calendar_event(self, event_datetime, description):
        event = {
            'summary': 'Rendez-vous WhatsApp',
            'description': description,
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'dateTime': (event_datetime.replace(hour=event_datetime.hour + 1)).isoformat(),
                'timeZone': 'Europe/Paris',
            },
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f'Événement créé: {event.get("htmlLink")}')
        except Exception as e:
            print(f"Erreur lors de la création de l'événement: {e}")

    def check_new_messages(self):
        try:
            # Récupérer les messages non lus
            unread_messages = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "unread"))
            )
            
            for message in unread_messages:
                message_text = message.text
                event_datetime = self.extract_date_time(message_text)
                
                if event_datetime:
                    self.create_calendar_event(event_datetime, message_text)
                    
        except Exception as e:
            print(f"Erreur lors de la lecture des messages: {e}")

    def run(self):
        while True:
            self.check_new_messages()
            time.sleep(60)  # Vérifier toutes les minutes

if __name__ == "__main__":
    bot = WhatsAppCalendarBot()
    bot.run() 