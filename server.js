const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);

app.use(express.static('public'));

io.on('connection', socket => {
    console.log('User connected');

    socket.on('joinGame', gameId => {
        socket.join(gameId);
        io.to(gameId).emit('message', 'A player joined the game');
    });

    socket.on('handThrow', data => {
        io.to(data.gameId).emit('updateHands', data);
    });

    socket.on('disconnect', () => console.log('User disconnected'));
});

const PORT = process.env.PORT || 3000;
http.listen(PORT, () => console.log(`Server running on port ${PORT}`));