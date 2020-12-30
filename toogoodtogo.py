from tgtg import TgtgClient
from pushsafer import init, Client
import schedule
import time
import os
import sys

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
      print("itemId {0} - Fehler! - {1}".format(itemID, sys.exc_info()))
  for item in client.get_items(favorites_only=True):
    try:
      checkItem(item)
    except:
      print("checkItem Fehler! - {0}".format(sys.exc_info()))
  print("new State: {0}".format(amounts))

schedule.every().minute.do(job)

job()
while True:
  try:
    schedule.run_pending()
  except:
    print("schedule Fehler! - {0}".format(sys.exc_info()))
  finally:
    time.sleep(10)

print("no schedule - exiting ...")

#checkItem(20282)  #Backwaren
#checkItem(20281)  #Obst & Gemüse
#client.get_item(20281)
#getItems()