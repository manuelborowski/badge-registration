
// From the server, get my (client, webbrowser) local ip address
export const get_my_ip = async  () => {
    const ret = await fetch(Flask.url_for('api.get_my_ip'), {headers: {'x-api-key': api_key}, signal: AbortSignal.timeout(2000) });
    const res = await ret.json();
    return res.ipaddress;
}

export const check_server_alive = async () => {
    try {
        const ret = await fetch(Flask.url_for('api.hb'), {signal: AbortSignal.timeout(2000) });
        if (localStorage.getItem("reboot") === "true") {
            localStorage.setItem("reboot", "false");
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
