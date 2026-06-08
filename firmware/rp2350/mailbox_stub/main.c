/**
 * RP2350 mailbox coprocessor stub — v2.0 bring-up
 * vFDD + VDU/GFX + HID + APU handshake (poll-based, no IRQ)
 * Core1 HDMI compose — TODO
 */
#include <stdint.h>
#include <string.h>

#define MB_BASE      0xFF00u
#define MB_STATUS    (MB_BASE + 0x00u)
#define MB_CMD       (MB_BASE + 0x01u)
#define MB_PARAM     (MB_BASE + 0x02u)
#define MB_AUX       (MB_BASE + 0x03u)
#define MB_BUFFER    (MB_BASE + 0x04u)

#define MB_ST_READY           0x01u
#define MB_ST_BUSY            0x02u
#define MB_ST_ERROR           0x04u
#define MB_ST_APU_READY       0x08u
#define MB_ST_HID_KEY_PENDING 0x10u
#define MB_ST_HID_MOUSE_PENDING 0x20u

#define CMD_NOP      0x00u
#define CMD_READ     0x01u
#define CMD_WRITE    0x02u

/* VDU text 0x10–0x17, GFX 0x20–0x26, system 0x30–0x31 — see docs/mailbox-protocol.md */
#define CMD_VDU_MIN  0x10u
#define CMD_VDU_MAX  0x31u

/* HID 0x40–0x43 — see docs/mailbox-protocol.md §2.5 */
#define CMD_HID_MIN  0x40u
#define CMD_HID_MAX  0x43u

/* APU PSG 0x50–0x53 — see docs/mailbox-protocol.md §2.4 */
#define CMD_APU_MIN  0x50u
#define CMD_APU_MAX  0x53u

static volatile uint8_t *const mb_status = (uint8_t *)MB_STATUS;
static volatile uint8_t *const mb_cmd = (uint8_t *)MB_CMD;
static volatile uint8_t *const mb_param = (uint8_t *)MB_PARAM;
static volatile uint8_t *const mb_aux = (uint8_t *)MB_AUX;
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

static void handle_vdu(uint8_t cmd)
{
    (void)cmd;
    (void)*mb_param;
    (void)*mb_aux;
    /* TODO: Core1 char_buf[25][40], bitmap 320x200, HSTX scan-out */
    mb_set_status(MB_ST_BUSY);
    mb_set_status(MB_ST_READY);
}

static void handle_hid(uint8_t cmd)
{
    (void)cmd;
    (void)*mb_param;
    /* TODO: Core0 TinyUSB HID → FIFO queues */
    mb_set_status(MB_ST_BUSY);
    mb_set_status(MB_ST_READY | MB_ST_APU_READY);
}

static void handle_apu(uint8_t cmd)
{
    (void)cmd;
    (void)*mb_param;
    /* TODO: Core0 PSG mix @ 22.05 kHz, PWM GPIO */
    mb_set_status(MB_ST_BUSY);
    mb_set_status(MB_ST_READY | MB_ST_APU_READY);
}

static int is_vdu_cmd(uint8_t cmd)
{
    return cmd >= CMD_VDU_MIN && cmd <= CMD_VDU_MAX;
}

static int is_hid_cmd(uint8_t cmd)
{
    return cmd >= CMD_HID_MIN && cmd <= CMD_HID_MAX;
}

static int is_apu_cmd(uint8_t cmd)
{
    return cmd >= CMD_APU_MIN && cmd <= CMD_APU_MAX;
}

int main(void)
{
    memset(sector_stub, 0xA5, sizeof(sector_stub));
    mb_set_status(MB_ST_APU_READY);

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
            if (is_vdu_cmd(cmd)) {
                handle_vdu(cmd);
            } else if (is_hid_cmd(cmd)) {
                handle_hid(cmd);
            } else if (is_apu_cmd(cmd)) {
                handle_apu(cmd);
            } else {
                mb_set_status(MB_ST_ERROR);
            }
            break;
        }
    }
}
