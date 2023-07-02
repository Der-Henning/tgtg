<!-- markdownlint-disable-next-line MD041 -->
## Webhook Openhab example

This configuration triggers an openhab switch every time new items are available.
I use it to make a LED lightstripe flash.

`docker-compose.yml` config:

```yml
environment:
    - WEBHOOK=true
    - WEBHOOK_URL=http://openhab.domain/rest/items/TGTG_New_Item
    - WEBHOOK_METHOD=POST
    - WEBHOOK_BODY=ON
    - WEBHOOK_TIMEOUT=60
```

Openhab item file `tgtg.items`:

```c
Switch TGTG_New_Item { expire="10s,command=OFF" }
```

You can expand the expire time to set the minimum interval between consecutive
events that will be triggered.

Openhab item file `led.items`:

```c
Group  LED_stripe

Switch LED_stripe_power "Power [%s]" (LED_stripe) {channel="wifiled:wifiled:wohnzimmer:power"}
Dimmer LED_stripe_white "White [%s]" (LED_stripe) {channel="wifiled:wifiled:wohnzimmer:white2"}
Color  LED_stripe_color "Color [%s]" (LED_stripe) {channel="wifiled:wifiled:wohnzimmer:color"}

// Temp Items
Switch LED_stripe_power_temp "temp Power [%s]" (LED_stripe)
Color  LED_stripe_color_temp "temp Color [%s]" (LED_stripe)
Dimmer LED_stripe_white_temp "temp White [%s]" (LED_stripe)
```

Of cause you have to adapt your channel.

Openhab rule file `tgtg.rules`:

```c
rule "TGTG Notification"
when
 Item TGTG_New_Item changed from OFF
then
 LED_stripe_color_temp.sendCommand(LED_stripe_color.state.toString)
 LED_stripe_power_temp.sendCommand(LED_stripe_power.state.toString)
 var i = 0
 while ((i=i+1) <= 3){
  LED_stripe_power.sendCommand(OFF)
  LED_stripe_color.sendCommand("0,100,100")
  Thread::sleep(800)
  LED_stripe_power.sendCommand(OFF)
  LED_stripe_color.sendCommand(LED_stripe_color_temp.state.toString)
  LED_stripe_power.sendCommand(LED_stripe_power_temp.state.toString)
  Thread::sleep(800)
 }
 Thread::sleep(800)
 LED_stripe_power.sendCommand(LED_stripe_power_temp.state.toString)
end
```

This will save the current state of the LED stripe, make 3 red flashes
and reset the previous settings.
