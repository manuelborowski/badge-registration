let filter_id;
let reset_button_cb = null;

export const create_filters = (id, filter_element, filters) => {
    if (filters.length > 0) {
        for (const filter of filters) {
            const label = document.createElement("label");
            filter_element.appendChild(label);
            if (filter.tt) label.setAttribute("title", filter.tt);
            if (filter.extra) {
                label.setAttribute("hidden", "hidden");
                label.classList.add("extra-filters");
            }
            label.style.marginRight = "10px";
            label.innerHTML = filter.label;
            if (filter.type === "select") {
                const select = document.createElement("select");
                label.appendChild(select);
                select.classList.add("form-control", "overview-filter");
                select.id = filter.name;
                if (filter.multiple) select.setAttribute("multiple", "multiple");
                for (const choice of filter.choices) {
                    const option = document.createElement("option");
                    select.appendChild(option);
                    option.value = choice[0];
                    option.innerHTML = choice[1];
                    if (choice[0] === filter.default) option.setAttribute("selected", "selected");
                }
            } else if (filter.type === "text" || filter.type === "date") {
                const input = document.createElement("input");
                label.appendChild(input);
                input.type = filter.type;
                input.id = filter.name;
                input.classList.add("form-control", "overview-filter")
            }
        }
        filter_id = id;
        const button = document.createElement("button");
        filter_element.appendChild(button);
        button.classList.add("btn", "btn-danger");
        button.type = "button";
        button.innerHTML = "Reset";
        button.addEventListener("click", () => {
            if (reset_button_cb) {
                const filter_settings = __load_filter_settings();
                __apply_filter_settings(true);
                reset_button_cb(filter_settings);
            } else {
                localStorage.clear(`${id}-filter`);
                location.reload();
            }
        })
        $(".overview-filter").change(() => __store_filter_settings());

        if (!__apply_filter_settings()) __store_filter_settings(); //filters are applied when the page is loaded for the first time
    }
}

export const subscribe_reset_button = cb => reset_button_cb = cb;

export const add_extra_filters = show_filters => {
    //Hide all extra filters
    const hide_filters = document.querySelectorAll(".extra-filters");
    for (const filter of hide_filters) {
        filter.setAttribute("hidden", "hidden");
        //Set a hidden filter to its default value, unless it is present in show_filters.
        if (filter.lastChild.type === "select-one") {
            const id = filter.lastChild.id;
            if (!show_filters.includes(id)) {
                for (const f of filters) {
                    if (f.name === id) {
                        filter.lastChild.value = f.default;
                        break;
                    }
                }
            }
        }
    }
    //Unhide wanted filters
    for (const filter of show_filters) {
        const filter_element = document.querySelector(`#${filter}`).parentElement;
        filter_element.removeAttribute("hidden");
    }
}

export const disable_filters = (filters) => {__set_filters_state(filters, false);}

export const enable_filters = (filters) => {__set_filters_state(filters, true);}

const __set_filters_state = (filters, state) => {
    if (!Array.isArray(filters)) filters = [filters];
    filters.forEach(filter => {
        filter.disabled = !state;
        filter.style.opacity = state ? "1": "0.5";
    })
}

//Store locally in the client-browser
function __store_filter_settings() {
    var filter_settings = [];
    if (filters.length > 0) {
        filters.forEach(f => {
            if (f.store === undefined || f.store === true) {
                if (f.type === 'select') {
                    filter_settings.push({name: f.name, type: f.type, value: document.querySelector(`#${f.name} option:checked`).value, default: f.default});
                } else if (f.type === 'checkbox') {
                    let boxes = [];
                    f.boxes.forEach(([k, l]) => {
                        boxes.push({id: k, checked: document.querySelector(`#${k}`).checked})
                    });
                    filter_settings.push({name: f.name, type: f.type, value: boxes, default: f.default})
                } else if (f.type === 'text' || f.type === 'date') {
                    filter_settings.push({name: f.name, type: f.type, value: document.querySelector(`#${f.name}`).value, default: f.default})
                }
            }
        });
        localStorage.setItem(`${filter_id}-filter`, JSON.stringify(filter_settings));
    }
}

function __apply_filter_settings(load_default_values=false) {
    var filter_settings = __load_filter_settings();
    if (filter_settings.length === 0) return false;
    filter_settings.forEach(f => {
        if (f.type === 'select' || f.type === 'text' || f.type === 'date') {
            const filter_element = document.querySelector(`#${f.name}`);
            if (filter_element) {
                if (f.type === "date") {
                    if (f.default === "today") {
                            let now = new Date();
                            filter_element.value = now.toISOString().split("T")[0];
                    }
                } else {
                    filter_element.value = load_default_values ? f.default : f.value;
                }
            }
        }
    })
    return true;
}

function __load_filter_settings() {
    if (filters.length === 0) return [];
    var filter_settings = JSON.parse(localStorage.getItem(`${filter_id}-filter`));
    if (!filter_settings) filter_settings = [];
    return filter_settings;
}