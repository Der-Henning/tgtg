from tgtg import TgtgClient
from pushsafer import init, Client
import schedule
import time
import os

itemIDs = []
TgTgLogin = os.getenv('TGTG_LOGIN')
TgTgPassword = os.getenv('TGTG_PASSWORD')
PushSaferKey = os.getenv('PUSHSAFER_KEY')
PushSaferDevice = os.getenv('PUSHSAFER_DEVICEID')

amounts = {}

# login with email and password
client = TgtgClient(email=TgTgLogin, password=TgTgPassword)
init(PushSaferKey)

def getItems():
  return client.get_items(
      favorites_only=False,
      latitude=53.542,
      longitude=10.214,
      radius=10,
  )

def sendMessage(message, title):
  print("Sending to {0}: {1}: {2}".format(PushSaferDevice, title, message))
  Client("").send_message(message,title,PushSaferDevice,"","","","","","","","","","","","","")

def checkItem(item):
  itemID = item["item"]["item_id"]
  amount = item["items_available"]
  display_name = item["display_name"]
  try:
    if amounts[itemID] == 0 and amount > amounts[itemID]:
      sendMessage("{0} Stück verfügbar!".format(amount), display_name)
  except:
    amounts[itemID] = amount
  finally:
    if amounts[itemID] != amount:
      print("{0} - New amount: {1}".format(display_name, amount))
      amounts[itemID] = amount

def job():
  print("Doing the job ...")
  for itemID in itemIDs:
    try:
      item = client.get_item(itemID)
      checkItem(item)
    except:
      print("{0} - Fehler!".format(itemID))
  for item in client.get_items(favorites_only=True):
    try:
      checkItem(item)
    except:
      print("Fehler!")

schedule.every().minute.do(job)

job()
while True:
  schedule.run_pending()
  time.sleep(1)

#checkItem(20282)  #Backwaren
#checkItem(20281)  #Obst & Gemüse
#client.get_item(20281)
#getItems()