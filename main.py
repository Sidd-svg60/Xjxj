# main.py
# Install dependencies: fastapi, uvicorn, websockets
# Run: uvicorn main:app --reload

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import random

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

# Store games: {game_id: {players: [ws1, ws2], moves: [], turn_index:0, max_turns:4, status:"waiting"}}
games = {}

@app.get("/")
async def get():
    with open("index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player_id = str(random.randint(1000,99999))
    current_game = None

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            game_id = data.get("gameId")
            num = data.get("num")

            # Host Game
            if action=="host":
                gid = str(random.randint(10000,99999))
                games[gid] = {"players":[{"id":player_id,"ws":websocket}], "moves":[], "turn_index":0, "max_turns":4, "status":"waiting"}
                current_game = gid
                await websocket.send_json({"action":"hosted","gameId":gid})

            # Join Game
            if action=="join":
                if game_id not in games or len(games[game_id]["players"])>=2:
                    await websocket.send_json({"action":"error","message":"Invalid or full game"})
                    continue
                games[game_id]["players"].append({"id":player_id,"ws":websocket})
                current_game = game_id
                await broadcast(game_id)

            # Start Game
            if action=="start":
                game = games.get(game_id)
                if game and len(game["players"])==2:
                    game["status"]="started"
                    await broadcast(game_id)

            # Player Move
            if action=="move":
                game = games.get(game_id)
                if not game or game["status"]!="started": continue
                if game["players"][game["turn_index"]]["id"] != player_id: continue
                game["moves"].append({"playerId":player_id,"num":num})
                game["turn_index"] = (game["turn_index"] + 1) % 2
                if len(game["moves"]) >= game["max_turns"]*2: game["status"]="finished"
                await broadcast(game_id)

    except WebSocketDisconnect:
        if current_game and current_game in games:
            games[current_game]["players"] = [p for p in games[current_game]["players"] if p["id"]!=player_id]
            await broadcast(current_game)

# Broadcast helper
async def broadcast(game_id):
    game = games.get(game_id)
    if not game: return
    data = {"action":"update","game":{"players":[p["id"] for p in game["players"]],"moves":game["moves"],"turnIndex":game["turn_index"],"maxTurns":game["max_turns"],"status":game["status"]}}
    for player in game["players"]:
        try:
            await player["ws"].send_json(data)
        except:
            pass