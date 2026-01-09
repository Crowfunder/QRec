import backend.components.workers.workerService

def test_generate_and_decrypt_secret_functional():
    worker_id = 67
    worker_name = "Six Seven"
    secret = backend.components.workers.workerService.generate_secret(worker_id, worker_name)
    data = backend.components.workers.workerService.decrypt_worker_secret(secret)

    # Asercja 1: Upewnij się, że odszyfrowane dane są słownikiem
    assert isinstance(data, dict)

    # Asercja 2: Sprawdź, czy kluczowe, NIESŁOSOWE dane się zgadzają
    assert data['worker_id'] == worker_id
    assert data['name'] == worker_name

    # Asercja 3: Sprawdź, czy losowa wartość w ogóle istnieje
    assert 'rand_value' in data
    assert len(data['rand_value']) == 6  # np. Sprawdź długość

def test_decrypt_secret():
    secret = 'gAAAAABpPdLUcBJbhCLwEX5HKf8mzB-sUIzAYQaQencHd--KaC4wbHRHlmdIfHSioWUMoZ_woRxjTsBVr30YQBRYv5xoicHjaERw2aGLvQ5Wgud1gaFNR7_zgTpNqzu96fsY-dQt3NvdRUXFmMKWiWV-9VgE99_HBg=='
    data = backend.components.workers.workerService.decrypt_worker_secret(secret)
    assert data['worker_id'] == 67
    assert data['name'] == "Six Seven"

