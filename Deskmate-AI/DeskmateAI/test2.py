import os
import warnings
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
warnings.filterwarnings('ignore')

print('Testing SpeechAuth...')
try:
    from backend.security.speech_auth import get_speech_auth
    auth = get_speech_auth()
    print('SpeechAuth OK')
except Exception as e:
    print(f'SpeechAuth FAILED: {e}')
    import traceback
    traceback.print_exc()

print('Testing RegistrationManager...')
try:
    from backend.security.registration import get_registration_manager
    reg = get_registration_manager()
    print('RegistrationManager OK')
except Exception as e:
    print(f'RegistrationManager FAILED: {e}')
    import traceback
    traceback.print_exc()

print('Testing AuthOrchestrator...')
try:
    from backend.security.auth_orchestrator import get_auth_orchestrator
    auth = get_auth_orchestrator()
    print('AuthOrchestrator OK')
except Exception as e:
    print(f'AuthOrchestrator FAILED: {e}')
    import traceback
    traceback.print_exc()

print('Done!')