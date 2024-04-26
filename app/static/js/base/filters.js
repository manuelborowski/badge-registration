let filter_id;

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
            localStorage.clear(`${id}-filter`);
            location.reload();
        })
        //if a filter is changed, then the filter is applied by simulating a click on the filter button
        $(".overview-filter").change(() => __store_filter_settings());

        if (!__load_filter_settings()) __store_filter_settings(); //filters are applied when the page is loaded for the first time
    }
}

export const add_extra_filters = filters => {
    //Hide all extra filters
    const hide_filters = document.querySelectorAll(".extra-filters");
    for (const filter of hide_filters ) {
        filter.setAttribute("hidden", "hidden");
    }
    //Unhide wanted filters
    for (const filter of filters) {
        const filter_element = document.querySelector(`#${filter}`).parentElement;
        filter_element.removeAttribute("hidden");
    }
}


//Store locally in the client-browser
function __store_filter_settings() {
    var filter_settings = [];
    if (filters.length > 0) {
        filters.forEach(f => {
            if (f.store === undefined || f.store === true) {
                if (f.type === 'select') {
                    filter_settings.push({
                        name: f.name,
                        type: f.type,
                        value: document.querySelector(`#${f.name} option:checked`).value
                    });
                } else if (f.type === 'checkbox') {
                    let boxes = [];
                    f.boxes.forEach(([k, l]) => {
                        boxes.push({id: k, checked: document.querySelector(`#${k}`).checked})
                    });
                    filter_settings.push({
                        name: f.name,
                        type: f.type,
                        value: boxes
                    })
                } else if (f.type === 'text' || f.type === 'date') {
                    filter_settings.push({
                        name: f.name,
                        type: f.type,
                        value: document.querySelector(`#${f.name}`).value
                    })
                }
            }
        });
        localStorage.setItem(`${filter_id}-filter`, JSON.stringify(filter_settings));
    }
}

function __load_filter_settings() {
    if (filters.length === 0) return true;
    var filter_settings = JSON.parse(localStorage.getItem(`${filter_id}-filter`));
    if (!filter_settings) {
        filter_settings = [];
        return false
    }
    filter_settings.forEach(f => {
        if (f.type === 'select' || f.type === 'text' || f.type === 'date') {
            const filter_element = document.querySelector(`#${f.name}`);
            if(filter_element) filter_element.value = f.value;
        }
    })
    return true;
}