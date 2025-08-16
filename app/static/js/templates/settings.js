export const setting_form = `
<link href="../static/css/form.css" rel="stylesheet">
<form id="setting-form">
    <div class="form-row">
        <hr style="width:100%">
        <b>Scan onderstaande QR code om gebruik te maken van je smartphone</b>
    </div>
    <div class="form-row" id="owner-row">
        <div class="form-element" style="width:100%">
            <img id="login-url-img" src="data:image/png;base64," alt="QR Code" width="200px" style="margin-left:auto;margin-right: auto;">
        </div>
    </div>
    <div class="form-row" id="owner-row">
        <div class="form-element">
            <label>Nieuwe QR code maken?<input type="checkbox" id="new-login-url-chk"></label>
        </div>
        <div class="form-element">
            <button id="new-login-url-btn" class="btn btn-success" disabled>Genereer nieuwe URL</button>
        </div>
    </div>
</form>`;
