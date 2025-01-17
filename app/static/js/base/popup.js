const popup_body = document.querySelector('#popup .modal-body');

export const init_popup = ({title = "", save_button = true, cancel_button = true, ok_button = false, width = "500px", default_button=null, default_input_element=null}={}) => {
    document.querySelector('#popup .modal-title').innerHTML = title;
    popup_body.replaceChildren();
    const popup_footer = document.querySelector('#popup .modal-footer');
    popup_footer.replaceChildren();
    popup_footer.innerHTML = ''
    if (ok_button) {popup_footer.innerHTML += '<button type="button" id="popup-btn-ok" class="btn btn-danger" data-dismiss="modal">Ok</button>'}
    if (save_button) {popup_footer.innerHTML += '<button type="button" id="popup-btn-save" class="btn btn-primary">Bewaren</button>'}
    if (cancel_button) {popup_footer.innerHTML += '<button type="button" id="popup-btn-cancel" class="btn btn-primary" data-dismiss="modal">Annuleer</button>'}
    if (default_button !== null && default_input_element !==null) {
        const btn = document.querySelector(`#popup-btn-${default_button}`);
        default_input_element.addEventListener("keyup", e => {
            if (e.key === "Enter") {
                btn.click();
            }
        });
    }
    document.querySelector(".modal-dialog").style.maxWidth = width;
}

export const hide_popup = () => {
    $('#popup').modal("hide");
}

export const show_popup = ({focus=null}) => {
    $('#popup').modal();
    if (focus !== null) setTimeout(() => focus.focus(), 500);
}

const save_button_event = cb => {
    document.querySelector('#popup .btn-primary').addEventListener('click', cb);
}

export const subscribe_btn_ok = (cb, opaque) => {
    document.querySelector('#popup-btn-ok').addEventListener('click', () => cb(opaque));
}

export const add_to_popup_body = child => {
    popup_body.appendChild(child)
}

const create_select_element = (label, id, name, options, attributes={}) => {
    const div_element = document.createElement('div');
    div_element.classList.add('popup-div')
    const label_element = document.createElement('label');
    label_element.innerHTML = label;
    label_element.htmlFor = id;
    const select_element = document.createElement('select');
    select_element.name = name;
    select_element.id = id;
    for (const [k, v] of Object.entries(attributes)) {select_element.setAttribute(k, v);}
    select_element.size = 1;
    let options_html = ''
    options.forEach(([v, l]) => {
        options_html += `<option value="${v}">${l}</option>`
    })
    select_element.innerHTML = options_html;
    div_element.appendChild(label_element);
    div_element.appendChild(document.createElement('br'));
    div_element.appendChild(select_element);
    return div_element;
}


export const create_input_element = (label, id, name, value=null, attributes={}) => {
    const div_element = document.createElement('div');
    div_element.classList.add('popup-div')
    const label_element = document.createElement('label');
    label_element.innerHTML = label;
    label_element.htmlFor = id;
    const input_element = document.createElement('input');
    input_element.name = name;
    input_element.id = id;
    if(value !== null)
        input_element.value = value;
    for (const [k, v] of Object.entries(attributes)) {input_element.setAttribute(k, v);}
    div_element.appendChild(label_element);
    div_element.appendChild(input_element);
    return div_element;
}


export const create_checkbox_element = (label, id, name, value=null, attributes={}) => {
    const div_element = document.createElement('div');
    div_element.classList.add('popup-div')
    const label_element = document.createElement('label');
    label_element.innerHTML = label;
    label_element.htmlFor = id;
    const input_element = document.createElement('input');
    input_element.name = name;
    input_element.type = "checkbox";
    input_element.id = id;
    if (value !== null)
        input_element.checked = value;
    for (const [k, v] of Object.entries(attributes)) {input_element.setAttribute(k, v);}
    div_element.appendChild(label_element);
    div_element.appendChild(input_element);
    return div_element;
}


export const create_p_element = (text) => {
    const p_element = document.createElement('p');
    p_element.innerHTML = text;
    return p_element
}

var formio_popup_form = null;
export const formio_popup_create = async (template, cb = null, defaults = null, opaque = null, width = null) => {
        const form_options = {sanitizeConfig: {addTags: ['iframe'], addAttr: ['allow'], ALLOWED_TAGS: ['iframe'], ALLOWED_ATTR: ['allow']},/* noAlerts: true,*/}
    //Render and display form
    $('#formio-popup').modal("show");
    if (width)
        document.querySelector('#formio-popup-dialog').style.maxWidth = width;
    formio_popup_form = await Formio.createForm(document.getElementById('formio-popup-content'), template, form_options)
    if (defaults != null) {
        Object.entries(defaults).forEach(([k, v]) => {
            try {
                formio_popup_form.getComponent(k).setValue(v);
            } catch (error) {
            }
    });
    }
    formio_popup_form.on('submit', async submitted => {
        $('#formio-popup').modal("hide");
        cb('submit', opaque, submitted.data);
    });
    formio_popup_form.on('cancel', () => {
        $('#formio-popup').modal("hide");
        cb('cancel', opaque)
    });
    formio_popup_form.on('clear', () => {
        $('#formio-popup').modal("hide");
        cb('clear', opaque)
    });
}

export const formio_popup_subscribe_event = (event, cb, opaque) => {
    formio_popup_form.on(event, async submitted => {
        cb(event, opaque, submitted);
    });
}

export const formio_popup_set_value = (key, value) => {
    try {
        formio_popup_form.getComponent(key).setValue(value);
    } catch (error) {
        console.log("skipped ", k, v);
    }
}