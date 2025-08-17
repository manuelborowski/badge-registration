
// From the server, get my (client, webbrowser) local ip address
export const get_my_ip = async  () => {
    // For some reason, the fetch can cause an error on the console: "Endpoint not found".
    // The error occurs when loading the students page, but not when loading the overview page???
    const ret = await fetch(Flask.url_for('api.get_my_ip'), {headers: {'x-api-key': api_key}, signal: AbortSignal.timeout(2000) });
    const res = await ret.json();
    return res.ipaddress;
}

// To make sure the client reloads when the server is rebooted, different mechanisms are implemented.
// On a development client (no webserver), the fetch throws an exception which is handled in the catch
// On a webserver, the fetch returns a status 502
// On a webserver, if the br-new service is restarted (sudo systemctl restart br-bew), this can happen so fast that the client does not perceive it correctly,
// i.e. the socketio is interrupted but it is not noticed by the catch or the 502.
// Therefore, the hb returns a timestamp from the server, which is changed each time the server reboots.  If the client notices the timestamp has changed, it reloads.
export const check_server_alive = async () => {
    try {
        const ret = await fetch(Flask.url_for('api.hb'));
        if (ret.status === 502) throw new Error(); // server says: bad gateway
        const status = await ret.json();
        if (localStorage.getItem("reboot") === "true" || localStorage.getItem("hb-timestamp") !== status.hb.toString()) {
            localStorage.setItem("reboot", "false");
            localStorage.setItem("hb-timestamp", status.hb);
            location.reload();
        }
    } catch  {
        localStorage.setItem("reboot", "true");
        document.querySelector("#formio-popup-content").innerHTML = "Systeem buiten dienst, even geduld aub..."
        $("#formio-popup").modal("show");
    }
    setTimeout(check_server_alive, 3000);
};

let timer_id = null;
export const timed_popup = (type, data, delay) => {
    if (timer_id !== null) clearTimeout(timer_id);
    document.querySelector("#formio-popup-content").innerHTML = data
    $("#formio-popup").modal("show");
    timer_id = setTimeout(() => $("#formio-popup").modal("hide"), delay);
}
