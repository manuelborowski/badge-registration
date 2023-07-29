export const badge_raw2hex = code => {
    const decode_caps_lock = code => {
        let out = '';
        const dd = {
            '&': '1', 'É': '2', '"': '3', '\'': '4', '(': '5', '§': '6', 'È': '7', '!': '8', 'Ç': '9',
            'À': '0', 'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F'
        };
        for (let r of code) {
            out += dd[r.toUpperCase()];
        }
        return out
    }

    const process_int_code = code_int => {
        if (code_int < 100000 || code_int > parseInt('FFFFFFFF', 16)) {
            return {is_rfid_code: false, code: code_int}
        }
        //convert the int to a hex number, add leading 0's (if required) to get 8 characters
        //revert the order of the 4 tupples (big to little endian)
        let hex = code_int.toString(16).toUpperCase();
        hex = '0'.repeat(8 - hex.length) + hex;
        hex = hex.split('');
        let out = []
        for (let i = 6; i >= 0; i -= 2) {
            out = out.concat(hex.slice(i, i + 2))
        }
        out = out.join('');
        return {is_rfid_code: true, code: out}
    }

    let is_rfid_code = true
    let is_valid_code = true
    code = code.toUpperCase().trim();

    if (code.length === 8) {
        // Asume a hex code of 8 chars
        if (code.includes('Q')) {
            // the badgereader is a qwerty HID device
            code = code.replace(/Q/g, 'A');
        }
        if (!/^[0-9a-fA-F]+$/.test(code)) {
            // it is not a valid hex code :-(  Check if capslock was on
            code = decode_caps_lock(code);
            if (!/^[0-9a-fA-F]+$/.test(code)) {
                // it is not a valid code :-(
                is_valid_code = is_rfid_code = false;
            }
        }
    } else {
        // Assume it is an integer code, so test it
        if (/^[0-9]+$/.test(code)) {
            const res = process_int_code(parseInt(code));
            is_rfid_code = res.is_rfid_code;
            code = res.code;
        } else {
            code = decode_caps_lock(code);
            if (/^[0-9]+$/.test(code)) {
                const res = process_int_code(parseInt(code));
                is_rfid_code = res.is_rfid_code;
                code = res.code;
            } else {
                is_valid_code = is_rfid_code = false;
            }
        }
    }
    return {valid: is_rfid_code, code}
}

