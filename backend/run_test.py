import sys
sys.path.append('.')

from tests.test_agent import TestInterviewStateMachine, TestMemoryManager

if __name__ == '__main__':
    sm_test = TestInterviewStateMachine()
    sm_test.setup_method()
    sm_test.test_stage_transitions()
    sm_test.test_get_stage_prompt_normal()
    sm_test.test_get_stage_prompt_with_rag()

    mm_test = TestMemoryManager()
    mm_test.test_empty_history()
    mm_test.test_small_history_kept_intact()
    mm_test.test_history_sliding_window_with_first_kept()
    mm_test.test_history_sliding_window_without_first_kept()
    print('All tests passed!')
