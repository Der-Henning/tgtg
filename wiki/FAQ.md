<!-- markdownlint-disable-next-line MD041 -->
## 1. I am getting Error 403 all the time

### Cause

If you see this error you where blocked from using the TGTG API.
It is usually caused by a too high request rate.
Since tools like this scanner violate the terms and conditions of TGTG
they try to detect the corresponding request patterns and block them.
These bans are usually temporary.

### Possible Solutions

1. Make sure you are using the latest version of the tgtg-scanner.
2. Increase the sleepTime (`config.ini`) or `SLEEP_TIME` (environment variable) between API requests.
3. Make sure you don't run multiple instances of the tgtg-scanner at the same time.
4. Try using a different IP. Most ISP provide a new IP when you reconnect your internet connection.
5. Wait some time. In most cases the error disappears after 24h.

## 2. How do I set up the tgtg-scanner in the Synology DSM Docker app?

Create the container as described in the official documentation
[Creating a Container](https://kb.synology.com/en-us/DSM/help/Docker/docker_container?version=7).
Set up the environment as described in the `docker-compose.yml`.
You don't have to set up any volumes.
The container will create a volume for persistent storage of your tgtg credentials by itself.

If you see the error `ERROR SAVING CREDENTIALS! - [ERRNO 13]` in your log
([#310](https://github.com/Der-Henning/tgtg/issues/310)),
the scanner has no permission to write the token files into the `/token` directory.
To fix the permission run `chown 1001:1001 /volume1/docker/tgtg/tokens` on your Synology.
You may need to adjust the path according to your setup.

## 3. How do I create a Telegram Bot?

You can create a new bot using @BotFather.
Simply start a conversation with @BotFather and send `/newbot`.
You will receive an API token for the bot. Enter this token in your config.
On the next start, the scanner will help you obtain the chat_id.

For more information about the @BotFather please refer to the official documentation:
<https://core.telegram.org/bots#6-botfather>

## 4. How does the reservation feature work?

Currently, the reservation feature only works with the Telegram bot included in the Telegram notifier.  
At the moment the bot cannot buy a Magic Bag.  
It can only reserve a Magic Bag and hold it for up to 5 minutes.  
After this time or when you cancel the reservation the bag will be available again.  

To buy the Magic Bag you have to cancel the reservation with the Telegram bot, which makes the item available again.  
Now you can click and buy it in the official Too Good To Go app.

The bot implements the following commands:
+ `/reserve`: Lists all your favorite Magic Bags and currently available amount. Click on an item to reserve it as soon as it becomes available. To reserve several Magic Bags from the same store at once click several times on the same item. For each time you click on the item, an additional Magic Bag will be added.
+ `/reserveall`: Creates reservations for all your favorite Magic Bags at once. The same as clicking manually on each item in the `/reserve` menu. If such a reservation already exists, an additional Magic Bag will be added to it.
+ `/reservations`: Lists all active reservations in your queue. Click on a reservation to cancel it with all Magic Bags included.
+ `/orders`: Lists all currently active orders that are active for up to 5 minutes. Click on an order to cancel it and release the item to buy it in the official Too Good To Go app.
+ `/cancelallreservations`: Cancels all reservations created in the `/reserve` or `/reserveall` menus. The same as clicking manually on each reservation in the `/reservations` menu.
+ `/cancelallorders`: Cancels all active orders visible in the `/orders` menu. The same as clicking on each order in the `/orders` menu.
+ `/cancelall`: Cancels all reservations and active orders. The same as doing `/cancelallreservations` and `/cancelallorders` at once.

When bags become available, it will reserve as many bags as you have in your queue in one order.  
If there are fewer available bags than you have in your queue it will reserve all available bags and the reservation will remain active with the remaining bags that haven't been reserved yet.  
If the order fails (e.g. sold out), the reservation amount will remain the same.

**Important!**  
Certain stores may have a maximum limit on bags per customer.  
Please ensure that the desired quantity for reservation from this store is allowed first.  
Otherwise, your reservation will keep failing with this log message (until canceled or reserved in smaller chunks):
```
WARNING  Order failed: (200, b'{"state":"OVER_USER_WINDOW_LIMIT"}')
```

## 5. Docker compose files

Using Docker compose or Portainer special characters (`$`, `{}`, ...) in environment variables need to be escaped.

Working example `TELEGRAM_BODY` using variables:

```yaml
- 'TELEGRAM_BODY=*$${{display_name}}*\n*Pickup*: $${{pickupdate}}\n*Order*: $${{link}}'
```
