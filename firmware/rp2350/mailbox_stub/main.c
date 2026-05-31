/**
 * RP2350 mailbox coprocessor stub — v2.0 bring-up
 * GPU/HID/vFDD sector handler (poll-based, no IRQ)
 */
#include <stdint.h>
#include <string.h>

#define MB_BASE      0xFF00u
#define MB_STATUS    (MB_BASE + 0x00u)
#define MB_CMD       (MB_BASE + 0x01u)
#define MB_PARAM     (MB_BASE + 0x02u)
#define MB_BUFFER    (MB_BASE + 0x04u)

#define MB_ST_READY  0x01u
#define MB_ST_BUSY   0x02u
#define MB_ST_ERROR  0x04u

#define CMD_NOP      0x00u
#define CMD_READ     0x01u
#define CMD_WRITE    0x02u

static volatile uint8_t *const mb_status = (uint8_t *)MB_STATUS;
static volatile uint8_t *const mb_cmd = (uint8_t *)MB_CMD;
static volatile uint8_t *const mb_param = (uint8_t *)MB_PARAM;
static uint8_t mb_buffer[248];

static uint8_t sector_stub[512];

static void mb_set_status(uint8_t flags)
{
    *mb_status = flags;
}

static void handle_read(uint8_t sector)
{
    (void)sector;
    mb_set_status(MB_ST_BUSY);
    memcpy(mb_buffer, sector_stub, sizeof(mb_buffer));
    mb_set_status(MB_ST_READY);
}

static void handle_write(uint8_t sector)
{
    (void)sector;
    mb_set_status(MB_ST_BUSY);
    memcpy(sector_stub, mb_buffer, sizeof(mb_buffer));
    mb_set_status(MB_ST_READY);
}

int main(void)
{
    memset(sector_stub, 0xA5, sizeof(sector_stub));
    mb_set_status(0);

    for (;;) {
        uint8_t cmd = *mb_cmd;
        if (cmd == CMD_NOP) {
            continue;
        }
        uint8_t param = *mb_param;
        *mb_cmd = CMD_NOP;

        switch (cmd) {
        case CMD_READ:
            handle_read(param);
            break;
        case CMD_WRITE:
            handle_write(param);
            break;
        default:
            mb_set_status(MB_ST_ERROR);
            break;
        }
    }
}
