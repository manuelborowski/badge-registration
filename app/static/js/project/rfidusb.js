// Handles the communication with the rfid-usb service

export class Rfid {
    static __managed_state = false;
    static __operational_state = false;
    static __connected_state = true;
    static state = {not_connected: 1, up: 2, down: 3};
    static __cb = null;

    static init = () => Rfid.__check_state_timer();

    static set_managed_state = state => {
        Rfid.__managed_state = state;
        Rfid.__process_state_change()
    }

    static set_location = async location => {
        try {
            const ret = await fetch(`${rfidusb_url}/location/${location}`, {method: 'POST'});
            const status = await ret.json();
            var state = status === "ok";
            if (rfidusb_br_url !== "" && state) {
                const encoded_url = encodeURIComponent(encodeURIComponent(rfidusb_br_url));
                const ret = await fetch(`${rfidusb_url}/url/${encoded_url}`, {method: 'POST'});
                const status = await ret.json();
                state = (status === "ok") && state;
            }
            if (rfidusb_br_key !== "" && state) {
                const ret = await fetch(`${rfidusb_url}/api_key/${rfidusb_br_key}`, {method: 'POST'});
                const status = await ret.json();
                state = (status === "ok") && state;
            }
            return state
        } catch (e) {
            return false
        }
    }

    static __process_state_change = async () => {
        if (Rfid.__operational_state) {
            try {
                const ret = await fetch(`${rfidusb_url}/active/${Rfid.__managed_state ? 1 : 0}`, {method: 'POST'});
                const status = await ret.json();
                Rfid.__operational_state = status === "ok";
            } catch (e) {
                Rfid.__connected_state = false;
                Rfid.__operational_state = false;
            }
        }
        if (Rfid.__cb !== null) {
            const state = Rfid.get_state();
            Rfid.__cb(state);
        }
    }

    static get_state = () => {
        let state = null;
        if (!Rfid.__connected_state) {
            state = Rfid.state.not_connected;
        } else if (Rfid.__managed_state && Rfid.__operational_state) {
            state = Rfid.state.up;
        } else {
            state = Rfid.state.down;
        }
        return state;
    }

    static subscribe_state_change_cb = (cb) => {Rfid.__cb = cb;}

    // if an RFID reader is attached to a USB port (status.port is e.g. COM4), activate the rfidusb server and show the select-location-button
    static __check_state_timer = async () => {
        try {
            var timeout = 2;
            const ret = await fetch(`${rfidusb_url}/serial_port`);
            const status = await ret.json();
            const operational_state = status.port !== "";
            if (operational_state !== Rfid.__operational_state) {
                Rfid.__operational_state = operational_state;
                Rfid.__connected_state= true;
                Rfid.__process_state_change();
            }
        } catch (e) {
            Rfid.__connected_state= false;
            Rfid.__operational_state = false;
            Rfid.__process_state_change();
            timeout = 5;
        }
        setTimeout( Rfid.__check_state_timer, timeout * 1000);
    }
}
