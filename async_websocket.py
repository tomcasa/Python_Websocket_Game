import asyncio
import websockets
import json
from datetime import datetime


import figlet_cmd
import text_game

MSG_TYPE_FIGLET = "figlet"
MSG_TYPE_SYSTEM = "system"


# Ensemble des clients connectés
CLIENTS = set()
SESSIONS = {}    # session_id → ws
players = {}   


async def send_to_session(session_id: str, payload: dict) -> bool:
    """Envoie un message à UNE session. Retourne True si envoyé."""
    ws = SESSIONS.get(session_id)
    if ws is None:
        print('no')
        return False        
    try:
        print('>>')
        if (not 'time' in payload) : 
            payload["time"] = _now()

        await ws.send(json.dumps(payload, ensure_ascii=False))
        return True
    except Exception:
        # connexion morte : on nettoie 
        SESSIONS.pop(session_id, None)
        CLIENTS.discard(ws)
        return False


async def broadcast(message:str ):
    """Envoie un message à tous les clients connectés."""
    #print(message)
    if isinstance(message, dict):
        if (not 'time' in message) : 
            message["time"] = _now()
        message = json.dumps(message, ensure_ascii=False)

    if CLIENTS:
        # asyncio.gather permet d'envoyer en parallèle
        await asyncio.gather(
            *(client.send(message) for client in CLIENTS),
            return_exceptions=True
        )

def _now():
    return datetime.now().strftime("%H:%M:%S")

async def handler(websocket):


    client_ext = websocket.request.headers.get("Sec-WebSocket-Extensions")
    print(f"Client demandait : {client_ext}")
    
    # Réponse du serveur (contient ce qui a été accepté)
    server_ext = websocket.response.headers.get("Sec-WebSocket-Extensions")
    print(f"Serveur a répondu : {server_ext}")
    
    if server_ext and "permessage-deflate" in server_ext:
        print("✅ permessage-deflate ACTIF")
    else:
        print("❌ pas de compression négociée")



    """Gère une connexion client."""
    session_id = str(websocket.id)
    CLIENTS.add(websocket)
    SESSIONS[session_id] = websocket    # dict : pour ciblage
    players[session_id] = {
        "pseudo" : f"anno{len(CLIENTS)}" , 
        "pos_x" : 0 ,  
        "slot" : None  ,          
    }
      

    print(f"[+] Nouveau client. {session_id} Total: {len(CLIENTS)}")
    
    try:
        # Message de bienvenue
        await websocket.send(json.dumps({
            "type": MSG_TYPE_SYSTEM,
            "text": "Bienvenue ! Envoyez votre pseudo avec /nick <nom> \n/figlet <texte> (ASCII art)\n/text_game start (Jeu mur de brique)",
            "time": _now()
        }))
        
        # Notifier les autres
        await broadcast({
            "type": MSG_TYPE_SYSTEM,
            "text": f"Un nouveau participant a rejoint le chat ",
            "time": _now()
        })
        
        async for raw_message in websocket:
            try:
                data = json.loads(raw_message)
                print( f"Client id:${websocket.id} {raw_message}" ) 
                text = data.get("text", "").strip()
                dtype = data.get("type", "").strip()
                 

                if text == "/text_game start":
                    started = await text_game_i.start(players[session_id]["pseudo"])

                    #await websocket.send(json.dumps({
                    await broadcast({
                        "type": "system",
                        "text": f"Jeu démarré 🎮 par {players[session_id]['pseudo']}" if started else "Le jeu tourne déjà.",
                    })
                    
                    text_game_i._wall.set_player(players)

                    continue

                if text == "/text_game stop":
                    stopped = await text_game_i.stop(players[session_id]["pseudo"])
                    #await send_to_session(session_id, {
                    await broadcast({
                        "type": "system",
                        "text": f"Jeu arrêté par {pseudo}" if stopped else "Aucun jeu en cours.",
                    })
                    continue

                if dtype == "keypress" :
                    if data["key"] == "right" : 
                        players[session_id]["pos_x"] = players[session_id]["pos_x"] +1 
                        text_game_i._ready = True

                    if data["key"] == "left" :                         
                        players[session_id]["pos_x"] = players[session_id]["pos_x"] -1 

                    
                    continue

                if text.startswith("/text_game"):
                    await send_to_session(session_id, {
                        "type": "system",
                        "text": "Usage : /text_game start | stop",
                    })
                    continue


                # Commande /nick pour changer de pseudo
                if text.startswith("/nick "):
                    new_pseudo = text[6:].strip() or "Anonyme"
                    old_pseudo = players[session_id]["pseudo"]
                    pseudo = new_pseudo
                    players[session_id]["pseudo"] = pseudo 
                    await broadcast(json.dumps({
                        "type": MSG_TYPE_SYSTEM,
                        "text": f"{old_pseudo} s'appelle maintenant {pseudo}",
                        "time": _now()
                    }))
                    continue
 
                            
                if text.startswith("/figlet"):
                    raw_args = text[len("/figlet"):].strip()

                    # Cas particulier : /figlet seul ou /figlet -h → aide
                    if not raw_args or raw_args in ("-h", "--help", "help"):
                        await send_to_session(session_id, {
                            "type": MSG_TYPE_SYSTEM,
                            "text": "Usage : /figlet [-f police] <texte>\n"
                                    f"Polices : {', '.join(sorted(figlet_cmd.ALLOWED_FONTS))}", # Polices : banner, big, block, bubble, digital, doom, larry3d, mini, ogre, rectangles, shadow, slant, small, smscript, smshadow, standard, starwars, stop, sub-zero, thin, univers
                            "time": _now(),
                        })
                        continue

                    try:
                        art = figlet_cmd.render_all(raw_args)
                        await broadcast(json.dumps({
                            "type": MSG_TYPE_FIGLET,
                            "pseudo": players[session_id]["pseudo"],
                            "text": art,
                            "font": figlet_cmd._parse_args(raw_args)[0],
                            "time": _now(),
                        }))
                    except figlet_cmd.FigletError_ as e:
                        await send_to_session(session_id, {
                            "type": MSG_TYPE_SYSTEM,
                            "text": str(e),
                            "time": _now(),
                        })
                    continue
                    
                
                # Message normal
                message = json.dumps({
                    "type": "message",
                    "pseudo": players[session_id]["pseudo"],
                    "text": text,
                    "time": _now()
                })
                await broadcast(message)
                
            except json.JSONDecodeError:
                print(f"Message invalide reçu: {raw_message}")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.discard(websocket)
        print(f"[-] Client déconnecté. Total: {len(CLIENTS)}")
        await broadcast(json.dumps({
            "type": MSG_TYPE_SYSTEM,
            "text": f"{players[session_id]["pseudo"]} a quitté le chat",
            "time": _now()
        }))
        
        players.pop(session_id)
        SESSIONS.pop(session_id)



text_game_i = None

async def main():
    
    global text_game_i
    text_game_i = text_game.TextGame(broadcast)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Serveur WebSocket démarré sur ws://localhost:8765")
        await asyncio.Future()  # tourne indéfiniment




if __name__ == "__main__":
    asyncio.run(main())


'''
 
/home/tk/py_env/dolce_tk/bin/python async_websocket.py 
'''