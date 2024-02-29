const context_wrapper = document.querySelector(".right-click-wrapper");
const context_menu = document.querySelector(".right-click-wrapper .menu");
const context_active_area = document.querySelector(".right-click-canvas");
let item_ids = 0;
let get_ids_cb = null;
let endpoint = null;

context_active_area.addEventListener("contextmenu", e => {
    e.preventDefault();
    e.stopImmediatePropagation();
    let x = e.x, y = e.y;
    let win_width = window.innerWidth;
    let win_height = window.innerHeight;
    let menu_width = context_wrapper.offsetWidth;
    let menu_height = context_wrapper.offsetHeight;
    if (context_menu !== null) {
        if (x > (win_width - menu_width - context_menu.offsetWidth)) {
            context_menu.style.left = "-200px";
        } else {
            context_menu.style.left = "";
            context_menu.style.right = "-200px";
        }
    }
    x = x > win_width - menu_width ? win_width - menu_width - 5 : x;
    y = y > win_height - menu_height ? e.pageY - menu_height - 5 : e.pageY;
    item_ids = []
    if (get_ids_cb) {
        item_ids = get_ids_cb(e);
    } else {
        console.log("context_active_area.addEventListener: no get_ids_cb configured")
    }
    context_wrapper.style.left = `${x}px`;
    context_wrapper.style.top = `${y}px`;
    context_wrapper.style.visibility = "visible";
});


const default_menu_template = {
    divider: {},
    text_input: {}
}

export const create_menu = (location, menu_template) => {
    context_menu.innerHTML = "";
    const menu_items = "menu" in locations[location] ? locations[location].menu :  ["delete"];
    menu_template = {...menu_template, ...default_menu_template};
    for (const mi of menu_items) {
        const item_template = menu_template[mi];
        const li = document.createElement("li");
        context_menu.appendChild(li);
        li.classList.add("item");
        const span = document.createElement("span");
        if(mi === "divider") {
            span.innerHTML = "--------------";
        } else if(mi === "text_input") {
            const input = document.createElement("input");
            span.appendChild(input);
        } else {
            li.onclick = () => item_clicked_with_cb(item_template.cb);
            if ("iconscout" in item_template) {
                const i = document.createElement("i");
                i.classList.add("uil", `uil-${item_template.iconscout}`);
                li.appendChild(i);
            }
            span.innerHTML = item_template.label;
        }
        li.appendChild(span);
    }
}

export const subscribe_get_ids = cb => get_ids_cb = cb;

export const set_endpoint = ep => endpoint = ep;

const item_clicked_with_cb = cb => cb(item_ids);

export function item_clicked(item) {
    if (item in right_click_cbs) {
        right_click_cbs[item](item, item_ids);
    } else if (endpoint) {
        $.getJSON(Flask.url_for(endpoint, {'jds': JSON.stringify({item, item_ids})}),
            function (data) {
                if ("message" in data) {
                    bootbox.alert(data.message);
                    // window.setTimeout(() => {bootbox.hideAll();},1000);
                } else if ("redirect" in data) {
                    if (data.redirect.new_tab) {
                        if ("ids" in data.redirect) {
                            data.redirect.ids.forEach(id => window.open(`${data.redirect.url}/[${id}]`, '_blank'))
                        } else {
                            window.open(data.redirect.url, '_blank')
                        }
                    } else {
                        if ('ids' in data.redirect) {
                            window.location = `${data.redirect.url}/[${data.redirect.ids.join(', ')}]`;
                        } else {
                            window.location = data.redirect.url;
                        }
                    }
                } else {
                    bootbox.alert('Sorry, er is iets fout gegaan');
                }
            }
        );
    } else {
        console.error("right_click: no endpoint defined")
    }
}

var right_click_cbs = {};
export function subscribe_right_click(item, cb) {
    right_click_cbs[item] = cb;
}

document.addEventListener("click", () => context_wrapper.style.visibility = "hidden");
document.addEventListener("contextmenu", () => context_wrapper.style.visibility = "hidden");

