from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import routers.validate.validate_utils as validate_utils
from pydantic import ValidationError
from utils.models import Validate
from dependencies import Token
import time

router = APIRouter()

token = Token()


@router.websocket("/mage/validate")
async def validate(websocket: WebSocket):
    await websocket.accept()

    try:
        if token.check_token_expired():
            token.update_token()
        if token.token == "":
            await websocket.send_json({"detail": "Failed to retrieve authentication token."})
            await websocket.close()
            return

        data = await websocket.receive_json()

        validated_data = Validate(**data)

        # Step 1: Create the pipeline
        pipeline_name = validate_utils.create_temp_pipeline(token.token)
        if not pipeline_name:
            await websocket.send_json({"detail": "Failed to create pipeline."})
            await websocket.close()
            return
        await websocket.send_json({"message": f"Pipeline created: {pipeline_name}"})

        # Step 2: Create a trigger for the pipeline
        if not validate_utils.create_temp_pipeline_trigger(pipeline_name, token.token):
            validate_utils.delete_temp_pipeline(pipeline_name, token.token)
            await websocket.send_json({"detail": "Failed to create pipeline trigger."})
            await websocket.close()
            return
        await websocket.send_json({"message": "Pipeline trigger created."})

        # Step 3: Create the blocks inside the pipeline
        # Assuming you have some predefined blocks to create

        if not validate_utils.create_block(pipeline_name, token.token, validated_data.block_type, validated_data.content):
            validate_utils.delete_temp_pipeline(pipeline_name, token.token)
            await websocket.send_json({"detail": "Failed to create blocks."})
            await websocket.close()
            return
        await websocket.send_json({"message": "Blocks created."})

        # Step 4: Run the pipeline
        if not validate_utils.run_temp_pipeline(pipeline_name, token.token):
            validate_utils.delete_temp_pipeline(pipeline_name, token.token)
            await websocket.send_json({"detail": "Failed to run the pipeline."})
            await websocket.close()
            return
        await websocket.send_json({"message": "Pipeline started."})

        counter = 0
        # Step 5: Loop and get the status of the run until it is either completed or failed
        while True:
            if counter > 100:
                break

            status = validate_utils.check_temp_pipeline_status(pipeline_name, token.token)
            if status in ["completed", "failed"]:
                if status == "completed":
                    await websocket.send_json({"success": "passed"})
                else:
                    await websocket.send_json({"success": "failed"})
                break
            await websocket.send_json({"message": f"Pipeline status: {status}"})
            counter += 1
            time.sleep(5)  # Poll every 5 seconds

        # Step 6: Delete the pipeline
        if not validate_utils.delete_temp_pipeline(pipeline_name, token.token):
            await websocket.send_json({"detail": "Failed to delete the pipeline."})
            await websocket.close()
            return
        await websocket.send_json({"message": "Pipeline deleted."})

    except WebSocketDisconnect:
        await websocket.send_json({"message": "Websocket disconnect successfully!"})
    except ValidationError:
        await websocket.send_json({"detail": "JSON validation error!"})
