#include "mbed.h"
#include "SLCD.h"
#include "tsi_sensor.h"

SLCD slcd;                                                           
TSIAnalogSlider slider(PTB16, PTB17, 100);      // touch sensor

PwmOut gLed(LED_GREEN);                             // pwm out
PwmOut rLed(LED_RED);

int main()  
{ 
    slcd.printf("lcd ");
    wait(2);                                                                   // delay 2 sec

    while (1) 
    { 
            slcd.CharPosition = 0;                                    // if we don't use it the value on the screen will be sliding
            slcd.printf("%1.2f",slider.readPercentage());  // print TSI_sensor value on LCD
            rLed = slider.readPercentage();                     // set TSI_value to the PWM linked with LED
            gLed = 1.0 - slider.readPercentage();
            wait_ms(10); 
    }
}