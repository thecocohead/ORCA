import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from ORCA.models import Match, ScoreSheet


class GameDataConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def getNextMatch(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').select_related('red1', 'red2', 'blue1', 'blue2').order_by('scheduledStartTime').first()
        if match is None:
            match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Scheduled').order_by('scheduledStartTime').first()
        match.scheduledStartTime = match.scheduledStartTime.isoformat()
        return match

    @database_sync_to_async
    def startMatch(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Scheduled').order_by('scheduledStartTime').first()
        if not match:
            return None
        match.status = 'Playing'
        redScoreSheet = ScoreSheet(artifacts=0, minorFouls=0, majorFouls=0, team1endgame=0, team2endgame=0)
        blueScoreSheet = ScoreSheet(artifacts=0, minorFouls=0, majorFouls=0, team1endgame=0, team2endgame=0)
        redScoreSheet.match = match
        blueScoreSheet.match = match
        match.redScoreSheet = redScoreSheet
        match.blueScoreSheet = blueScoreSheet
        redScoreSheet.save()
        blueScoreSheet.save()
        match.save()
        return match

    @database_sync_to_async
    def isPlayingMatch(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if not match:
            return False
        return True

    @database_sync_to_async
    def addFoul(self, eventCode, eventSeason, team, severity, negated):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        foulCount = 1
        if match is None:
            return None

        if negated:
            foulCount = -1

        if team == 'red':
            scoresheet = match.redScoreSheet
        elif team == 'blue':
            scoresheet = match.blueScoreSheet
        else:
            return None
        if severity == 'minor':
            scoresheet.minorFouls += foulCount
        elif severity == 'major':
            scoresheet.majorFouls += foulCount
        else:
            return None
        scoresheet.save()

        return match

    @database_sync_to_async
    def getCurrentFouls(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        redScoreSheet = match.redScoreSheet
        blueScoreSheet = match.blueScoreSheet
        if redScoreSheet is None or blueScoreSheet is None:
            return None
        return redScoreSheet.minorFouls, blueScoreSheet.minorFouls, redScoreSheet.majorFouls, blueScoreSheet.majorFouls

    @database_sync_to_async
    def getScores(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        redScoreSheet = match.redScoreSheet
        blueScoreSheet = match.blueScoreSheet
        if redScoreSheet is None or blueScoreSheet is None:
            return None
        redTotal = redScoreSheet.artifacts * 1 + redScoreSheet.minorFouls * -3 + redScoreSheet.majorFouls * -5
        if redScoreSheet.team1endgame == 1:
            redTotal += 10
        elif redScoreSheet.team1endgame == 2:
            redTotal += 20
        if redScoreSheet.team2endgame == 1:
            redTotal += 10
        elif redScoreSheet.team2endgame == 2:
            redTotal += 20
        blueTotal = blueScoreSheet.artifacts * 1 + blueScoreSheet.minorFouls * -3 + blueScoreSheet.majorFouls * -5
        if blueScoreSheet.team1endgame == 1:
            blueTotal += 10
        elif blueScoreSheet.team1endgame == 2:
            blueTotal += 20
        if blueScoreSheet.team2endgame == 1:
            blueTotal += 10
        elif blueScoreSheet.team2endgame == 2:
            blueTotal += 20
        return redTotal, blueTotal

    @database_sync_to_async
    def getTeams(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        return match.red1_id, match.red2_id, match.blue1_id, match.blue2_id

    @database_sync_to_async
    def endGameUpdate(self, eventCode, eventSeason, team):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        if team == 'blue1':
            match.blueScoreSheet.team1endgame += 1
            if match.blueScoreSheet.team1endgame == 3:
                match.blueScoreSheet.team1endgame = 0
        elif team == 'blue2':
            match.blueScoreSheet.team2endgame += 1
            if match.blueScoreSheet.team2endgame == 3:
                match.blueScoreSheet.team2endgame = 0
        elif team == 'red1':
            match.redScoreSheet.team1endgame += 1
            if match.redScoreSheet.team1endgame == 3:
                match.redScoreSheet.team1endgame = 0
        elif team == 'red2':
            match.redScoreSheet.team2endgame += 1
            if match.redScoreSheet.team2endgame == 3:
                match.redScoreSheet.team2endgame = 0
        else:
            return None
        match.redScoreSheet.save()
        match.blueScoreSheet.save()

    @database_sync_to_async
    def getEndGame(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        return match.blueScoreSheet.team1endgame, match.blueScoreSheet.team2endgame, match.redScoreSheet.team1endgame, match.redScoreSheet.team2endgame

    @database_sync_to_async
    def finalizeScores(self, eventCode, eventSeason):
        match = Match.objects.filter(event__code=eventCode, event__season=eventSeason, status='Playing').order_by('scheduledStartTime').first()
        if match is None:
            return None
        match.status = 'Committed'
        match.save()
        return match

    async def connect(self):
        self.room_group_name = 'game_data'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.close()

    async def findNextMatch(self, body):
        eventCode = body['eventCode']
        eventSeason = body['eventSeason']
        if not eventCode or not eventSeason:
            await self.send(text_data=json.dumps({
                'action': 'ERROR',
                'error': 'Missing eventCode/eventSeason',
            }))
            return
        nextMatch = await self.getNextMatch(eventCode, eventSeason)
        if nextMatch is None:
            await self.send(text_data=json.dumps({
                'action': 'ERROR',
                'error': 'No matches found',
            }))
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'CURRENT_MATCH',
            'data': {
                'phase': nextMatch.phase,
                'number': nextMatch.number,
                'startTime': nextMatch.scheduledStartTime,
                'red1': nextMatch.red1_id,
                'red2': nextMatch.red2_id,
                'blue1': nextMatch.blue1_id,
                'blue2': nextMatch.blue2_id,
            }
        })

    async def stateUpdate(self, body):
        isMatchOngoing = await self.isPlayingMatch(body['eventCode'], body['eventSeason'])
        if isMatchOngoing:
            red1, red2, blue1, blue2 = await self.getTeams(body['eventCode'], body['eventSeason'])
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'STATE_UPDATE',
                'data': {
                    'isMatchOngoing': True,
                    'red1': red1,
                    'red2': red2,
                    'blue1': blue1,
                    'blue2': blue2,
                }
            })
        else:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'STATE_UPDATE',
                'data': {
                    'isMatchOngoing': False
                }
            })

    async def foulCountUpdate(self, body):
        foulCounts = await self.getCurrentFouls(body['eventCode'], body['eventSeason'])
        if foulCounts is None:
            return
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'FOUL_UPDATE',
            'data': {
                'redMinors': foulCounts[0],
                'blueMinors': foulCounts[1],
                'redMajors': foulCounts[2],
                'blueMajors': foulCounts[3],
            }
        })

    async def updateScores(self, body):
        scores = await self.getScores(body['eventCode'], body['eventSeason'])
        if scores is None:
            return
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'SCORE_UPDATE',
            'data': {
                'redScore': scores[0],
                'blueScore': scores[1],
            }
        })

    async def sendEndGame(self, eventCode, eventSeason):
        endGame = await self.getEndGame(eventCode, eventSeason)
        if endGame is None:
            return
        await self.send(text_data=json.dumps({
            'action': 'ENDGAME_STATE',
            'data': {
                'blue1': endGame[0],
                'blue2': endGame[1],
                'red1': endGame[2],
                'red2': endGame[3],
            }
        }))



    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']
        body = data['data']

        if action == 'REFEREE_JOIN':
            await self.findNextMatch(body)
            await self.stateUpdate(body)
            await self.foulCountUpdate(body)

        if action == 'DISPLAY_JOIN':
            await self.findNextMatch(body)
            await self.stateUpdate(body)

        if action =='MATCH_START':
            await self.startMatch(body['eventCode'], body['eventSeason'])
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'MATCH_START',
            })
            await self.stateUpdate(body)

        if action == 'FOUL':
            await self.addFoul(body['eventCode'], body['eventSeason'], body['team'], body['severity'], body['negated'])
            await self.foulCountUpdate(body)
            await self.updateScores(body)

        if action == 'ENDGAME_UPDATE':
            await self.endGameUpdate(body['eventCode'], body['eventSeason'], body['team'])
            await self.sendEndGame(body['eventCode'], body['eventSeason'])
            await self.updateScores(body)

        if action == 'COMMIT':
            await self.finalizeScores(body['eventCode'], body['eventSeason'])
            await self.stateUpdate(body)
            await self.findNextMatch(body)

    async def MATCH_START(self, event):
        await self.send(text_data=json.dumps({
            'action': 'MATCH_START',
        }))

    async def CURRENT_MATCH(self, event):
        await self.send(text_data=json.dumps({
            'action': 'CURRENT_MATCH',
            'data': event.get('data')
        }))


    async def FOUL_UPDATE(self, event):
        await self.send(text_data=json.dumps({
            'action': 'FOUL_UPDATE',
            'data': event.get('data')
        }))

    async def STATE_UPDATE(self, event):
        await self.send(text_data=json.dumps({
            'action': 'STATE_UPDATE',
            'data': event.get('data')
        }))
    async def SCORE_UPDATE(self, event):
        await self.send(text_data=json.dumps({
            'action': 'SCORE_UPDATE',
            'data': event.get('data')
        }))