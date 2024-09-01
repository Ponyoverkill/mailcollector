// const baseUrl = window.location.host
const baseUrl = 'http://127.0.0.1'
const soketUrl = 'http://127.0.0.1:3301'

const urls = {
    // token: baseUrl + "/api/v1/token/",
    ws: soketUrl + "/ws/status/",
    messages: baseUrl + "/api/v1/messages/",
    mails: baseUrl + "/api/v1/mails/"
}

class MailService{
    static url = urls.mails

    constructor(token, application) {
        this.token = token
        this.application = application
    }

    async login(email, password, service){
        const data = {
            username: email,
            password: password,
            service: service
        }

        const resp = await fetch(urls.mails, {
            method: "POST",
            cache: "no-cache",
            headers: {
              "Accept": "application/json",
              "Content-Type":"application/json",
            },
            body: JSON.stringify(data),
          });

        if (resp.status == 201) {
            this.application.loginForm.show_logout_button()
            this.token = (await resp.json()).token
            localStorage.setItem("token", this.token)
        } else {
            alert("wrong username or password")
            this.application.loginForm.show_login_form()
            this.token = null
            localStorage.removeItem("token")
        }

        return resp
    }

    async login_by_token(token){

        const data = {
            token: token
        }

        const resp = await fetch(urls.mails, {
            method: "POST",
            cache: "no-cache",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json"
            },
            body: JSON.stringify(data),
          });

        if (resp.status == 201){
            this.application.loginForm.show_logout_button()
            this.token = (await resp.json()).token
            localStorage.setItem("token", this.token)
        } else {
            this.application.loginForm.show_login_form()
            this.token = null
            localStorage.removeItem("token")
        }
    }

}


class MailComponent{
    constructor(application) {
        this.element = $("div.auth")
        this.application = application
    }

    show_login_form() {
        this.element.html('<select id="service">' +
            '<option value="YANDEX">yandex</option>' +
            '<option value="GOOGLE">google</option>' +
            '<option value="MAIL">mail</option>' +
            '</select>' +
            '<input type="text" id="username"/>' +
            '<input type="password" id="password">' +
            '<button id="login">login</button>')

        const el = this
        $("#login").click(async (event) => {await el.login()})
    }

    hide_login_form(){
        this.show_logout_button()
    }

    async login(){
        const username = $('#username').val()
        const password = $('#password').val()
        const service = $('#service').val()
        await this.application.mailService.login(username, password, service)
    }

    show_logout_button(){
        this.element.html('<button id="logout">logout</button>')

        const el = this

        $("#logout").click(async (event) => {
            localStorage.removeItem("token")
            await el.show_login_form();
            await el.application.messageComponent.clear()
            await el.application.statusComponent.clear()
        })
        this.application.statusComponent.show_load_button()
    }

    hide_logout_button(){
        this.show_login_form()
    }
}


class StatusComponent{
    constructor(application) {
        this.application = application
        this.element = $("div.status")
    }

    show_load_button(){
        this.element.children("div.action").html('<button id="load_button">load</button>')
        $('#load_button').click(async (event) => {
            await this.application.statusService.consume(this.application.mailService.token)
            this.hide_load_button()
        })

    }

    async show_numbers(count, number){
        this.element.children("div.number").html("<a>searching "+ number + " of " + count + "</a>")
    }

    hide_numbers(){
        this.element.children("div.number").html("")
    }

    async show_status(count, number){
        this.element.children("div.spinner").html("<a>loading " + number + " messages left</a>")
    }

    hide_status(){
        this.element.children("div.spinner").html("")
    }

    hide_load_button(){
        this.element.children("div.action").html('')
    }

    async clear(){
        this.hide_numbers()
        this.hide_status()
    }
}


class StatusService{
    constructor(application) {
        this.application = application
    }

    async consume(token){
        const socket = new WebSocket(urls.ws + "?token=" + token)
        this.chatSocket = socket
        const el = this

        this.chatSocket.onopen = function (ev) {
            socket.send(JSON.stringify({"data": null, "action": "start"}))
        }

        this.chatSocket.onmessage = async function(e) {
            const data = JSON.parse(e.data);
            if (data["type"] == "finding_last"){
                await el.application.statusComponent.show_numbers(data["message"]["count"], data["message"]["number"])
            } else if (data["type"] == "load_message"){
                await el.application.statusComponent.show_status(data["message"]["count"], data["message"]["number"])
                await el.application.messageComponent.add_message(data["message"]["data"])
            }
        };

        this.chatSocket.onclose = async function(e) {
            console.error('Chat socket closed unexpectedly');
        };
        // this.chatSocket.send(JSON.stringify({"message": 123}))
    }

}


class MessageComponent{
    constructor(application) {
        this.application = application
        this.element = $("div.data")
        this.element.html("<table><tr><td>id</td><td>subject</td><td>dispatch</td><td>receipt</td><td>text</td><td>files</td></tr></table>")
        // this.element.children("table").html(html)
    }

    async add_message(data){
        let html = ""
        html += "<tr class=\"data-tr\">"
        html += "<td>" + data["id"] + "</td>"
        html += "<td>" + data["subject"] + "</td>"
        html += "<td>" + data["dispatch"] + "</td>"
        html += "<td>" + data["receipt"] + "</td>"
        html += "<td>" + this.sanitize(data["text"]) + "</td>"
        html += "<td>"
        for (let file of data["files"]){
            html += "<a href=\""+ file+ "\">" + file +"</a>"
        }
        html += "</td>"
        html += "</tr>"
        // console.log(this.element.children("table").children('tr:last'))
        this.element.children("table").find("tr").last().after(html);
    }

    sanitize(str) {
        return str.replace(/[&<>"'`]/g, char => this.escapeHtml[char]);
    }

    escapeHtml(str) {
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/`/g, '&#x60;');
    }

    async clear(){
        this.element.html("<table><tr><td>id</td>subject<td>dispatch</td><td>receipt</td><td>text</td><td>files</td></tr></table>")
    }
}

class Application{
    constructor(token) {
        this.mailService = new MailService(token, this)
        this.loginForm = new MailComponent(this)

        this.statusComponent = new StatusComponent(this)
        this.statusService = new StatusService(this)
        this.messageComponent = new MessageComponent(this)

        this.token = token
    }

    async start(){
        await this.mailService.login_by_token(this.token)
    }
}


async function onload(){
    let token = localStorage.getItem("token")
    const application = new Application(token)
    await application.start()
}

$(document).ready(onload)