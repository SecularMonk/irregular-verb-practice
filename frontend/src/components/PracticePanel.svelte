<script lang="ts">
  import { createExercise, submitAttempt, type AttemptResponse, type ExerciseResponse } from "../lib/api";

  export let disabled = false;
  export let onAttemptSaved: (() => void) | undefined = undefined;

  let difficulty = 1;
  let exercise: ExerciseResponse | null = null;
  let userAnswer = "";
  let result: AttemptResponse | null = null;
  let isLoadingExercise = false;
  let isSubmitting = false;
  let errorMessage = "";

  async function handleGenerateExercise() {
    isLoadingExercise = true;
    errorMessage = "";
    result = null;
    userAnswer = "";

    try {
      exercise = await createExercise(difficulty);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to generate exercise.";
    } finally {
      isLoadingExercise = false;
    }
  }

  async function handleSubmitAnswer() {
    if (!exercise || !userAnswer.trim()) return;
    isSubmitting = true;
    errorMessage = "";

    try {
      result = await submitAttempt(exercise.id, userAnswer.trim());
      onAttemptSaved?.();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to submit answer.";
    } finally {
      isSubmitting = false;
    }
  }
</script>

<section class="panel">
  <h2>Practice</h2>

  <div class="field-row">
    <label for="difficulty">Difficulty</label>
    <select id="difficulty" bind:value={difficulty} disabled={disabled || isLoadingExercise || isSubmitting}>
      <option value={1}>1</option>
      <option value={2}>2</option>
      <option value={3}>3</option>
    </select>
    <button on:click={handleGenerateExercise} disabled={disabled || isLoadingExercise || isSubmitting}>
      {isLoadingExercise ? "Generating..." : "Generate Exercise"}
    </button>
  </div>

  {#if exercise}
    <div class="exercise-box">
      <p>{exercise.prompt}</p>
      <div class="field-row">
        <input
          type="text"
          bind:value={userAnswer}
          placeholder="Type your answer"
          disabled={disabled || isSubmitting}
        />
        <button on:click={handleSubmitAnswer} disabled={disabled || isSubmitting || !userAnswer.trim()}>
          {isSubmitting ? "Submitting..." : "Submit"}
        </button>
      </div>
    </div>
  {/if}

  {#if result}
    <div class="result-box">
      <p><strong>{result.is_correct ? "Correct" : "Incorrect"}</strong></p>
      <p>Correct answer: {result.corrected_answer}</p>
      <p>{result.explanation}</p>
    </div>
  {/if}

  {#if errorMessage}
    <p class="error">{errorMessage}</p>
  {/if}
</section>
