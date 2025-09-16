import json
import time

def lambda_handler(event, context):
    """SSE debate stream handler"""
    
    try:
        # Generate SSE stream data
        events = []
        
        # Start event
        events.append("event: debate.start\ndata: {\"message\": \"Starting debate\"}\n\n")
        
        # Argument events
        agents = ['Legal', 'Finance', 'Compliance']
        for agent in agents:
            data = {
                "agent": agent,
                "argument": f"This is {agent} agent's argument",
                "timestamp": time.time()
            }
            events.append(f"event: debate.argument\ndata: {json.dumps(data)}\n\n")
        
        # Consensus event
        consensus_data = {
            "consensus": "All agents have reached agreement",
            "timestamp": time.time()
        }
        events.append(f"event: debate.consensus\ndata: {json.dumps(consensus_data)}\n\n")
        
        # Complete event
        events.append("event: debate.complete\ndata: [DONE]\n\n")
        
        # Join all events
        stream_data = "".join(events)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/event-stream',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            },
            'body': stream_data
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }