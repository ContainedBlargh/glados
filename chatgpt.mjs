import bodyParser from 'body-parser';
import { ChatGPTAPIBrowser as _ChatGPTAPIBrowser } from 'chatgpt';
const ChatGPTAPIBrowser = _ChatGPTAPIBrowser;
import { config } from 'dotenv';
import express from 'express';

config()

const app = express();

app.use(express.json());

const api = new ChatGPTAPIBrowser({
    email: process.env.email,
    password: process.env.password,
    isGoogleLogin: false
})

app.post('/', async (req, res) => {
    
    if (!req.body || !req.body.query) {
        console.log(`Received: '${JSON.stringify(req.body)}'`)
        res.status(400)
        res.send("")
        return
    }
    const prompt = req.body.query
    if (!(await api.getIsAuthenticated())) {
        await api.initSession();
    }
    if (!!req.body.reset) {
        api.resetThread()
    }
    const responseObject = await api.sendMessage(prompt)
    console.log(responseObject)
    res.send(responseObject.response)
})

api.initSession()
app.listen(3000)
