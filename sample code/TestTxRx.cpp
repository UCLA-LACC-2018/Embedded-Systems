#include "mbed.h"
#include "nRF24L01P.h"

Serial pc(USBTX, USBRX); // tx, rx
//nRF24L01P my_nrf24l01p(p5, p6, p7, p8, p9, p10);    // mosi, miso, sck, csn, ce, irq
 nRF24L01P my_nrf24l01p(PTA16, // mosi
                        PTA17, // miso
                        PTA15, // sck
                         PTD2   , //CSN
                         PTA13   , // CE
                        PTD4    // IRQ
                        );

DigitalOut led1(LED1);
DigitalOut led2(LED2);
//DigitalOut led3(LED3);
//DigitalOut led4(LED4);

int main() {
    
    // set up PC comm.
    //pc.baud(115200);
    
    // set up wireless transfer size
    #define TRANSFER_SIZE 4

    char rxData[TRANSFER_SIZE];
    int rxDataCnt = 0;
    char txData[TRANSFER_SIZE];
    int txDataCnt = 0;

    // initialize wireless comm.
    my_nrf24l01p.powerUp();
    my_nrf24l01p.setTransferSize( TRANSFER_SIZE );
    my_nrf24l01p.setReceiveMode();
    my_nrf24l01p.enable();
    my_nrf24l01p.setAirDataRate(2000);
    // set wireless RX
    //my_nrf24l01p.setRxAddress(0xABCDABCDABCDABCD);
    
    // Display the (default) setup of the nRF24L01+ chip
    pc.printf( "nRF24L01+ Frequency    : %d MHz\r\n",  my_nrf24l01p.getRfFrequency() );
    pc.printf( "nRF24L01+ Output power : %d dBm\r\n",  my_nrf24l01p.getRfOutputPower() );
    pc.printf( "nRF24L01+ Data Rate    : %d kbps\r\n", my_nrf24l01p.getAirDataRate() );
    pc.printf( "nRF24L01+ TX Address   : 0x%010llX\r\n", my_nrf24l01p.getTxAddress() );
    pc.printf( "nRF24L01+ RX Address   : 0x%010llX\r\n", my_nrf24l01p.getRxAddress() );

    while (1) {
        // If we've received anything over the host serial link...
        if ( pc.readable() ) {
 
            // ...add it to the transmit buffer
            txData[txDataCnt++] = pc.getc();
            pc.printf( "%d,", txData[txDataCnt] );
 
            // If the transmit buffer is full
            if ( txDataCnt >= sizeof( txData ) ) {
 
                // Send the transmitbuffer via the nRF24L01+
                my_nrf24l01p.write( NRF24L01P_PIPE_P0, txData, txDataCnt );
 
                txDataCnt = 0;
            }
 
            // Toggle LED1 (to help debug Host -> nRF24L01+ communication)
            led1 = !led1;
        }
        // If we've received anything in the nRF24L01+...
        if ( my_nrf24l01p.readable() ) {

            // ...read the data into the receive buffer
            rxDataCnt = my_nrf24l01p.read( NRF24L01P_PIPE_P0, rxData, sizeof( rxData ) );

            // Display the receive buffer contents via the host serial link
            for ( int i = 0; rxDataCnt > 0; rxDataCnt--, i++ ) {
                pc.printf( "%d,", rxData[i] );
            }
            pc.printf("\n\r");

            // Toggle LED2 (to help debug nRF24L01+ -> Host communication)
            led2 = !led2;
        }
    }
}
