import json
import logging
from modules.init import load_deepfilter_model

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

model, df_state = None, None

def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")
    
    global model, df_state
    
    try:
        # Load model if not already loaded
        if model is None or df_state is None:
            model, df_state = load_deepfilter_model(model, df_state)
        
        logger.info("DeepFilter model loaded successfully")
        return {
            'success': True,
            'message': 'DeepFilter model loaded successfully'
        }
    except Exception as e:
        logger.error(f"Error loading DeepFilter model: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'Error loading DeepFilter model: {str(e)}'
        }
