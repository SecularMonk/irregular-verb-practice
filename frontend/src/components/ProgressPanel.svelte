<script lang="ts">
  import { getProgress, type ProgressResponse } from "../lib/api";

  export let disabled = false;
  export let refreshToken = 0;

  let progress: ProgressResponse | null = null;
  let isLoading = false;
  let errorMessage = "";
  let lastRefreshToken = -1;

  async function loadProgress() {
    if (disabled) return;
    isLoading = true;
    errorMessage = "";

    try {
      progress = await getProgress();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to load progress.";
    } finally {
      isLoading = false;
    }
  }

  $: if (!disabled && refreshToken !== lastRefreshToken) {
    lastRefreshToken = refreshToken;
    loadProgress();
  }
</script>

<section class="panel">
  <h2>Progress</h2>

  <button on:click={loadProgress} disabled={disabled || isLoading}>
    {isLoading ? "Refreshing..." : "Refresh Progress"}
  </button>

  {#if progress}
    <div class="stats">
      <p>Attempts: {progress.overall_attempts}</p>
      <p>Correct: {progress.correct_answers}</p>
      <p>Success rate: {progress.success_rate}%</p>
    </div>

    <div class="stats">
      <h3>By Difficulty</h3>
      <p>
        D1: {progress.by_difficulty["1"]?.correct_answers ?? 0}/{progress.by_difficulty["1"]?.attempts ?? 0}
        ({progress.by_difficulty["1"]?.success_rate ?? 0}%)
      </p>
      <p>
        D2: {progress.by_difficulty["2"]?.correct_answers ?? 0}/{progress.by_difficulty["2"]?.attempts ?? 0}
        ({progress.by_difficulty["2"]?.success_rate ?? 0}%)
      </p>
      <p>
        D3: {progress.by_difficulty["3"]?.correct_answers ?? 0}/{progress.by_difficulty["3"]?.attempts ?? 0}
        ({progress.by_difficulty["3"]?.success_rate ?? 0}%)
      </p>
    </div>

    <div class="stats">
      <h3>Recent Attempts</h3>
      {#if progress.recent_attempts.length === 0}
        <p>No attempts yet.</p>
      {:else}
        <ul class="recent-list">
          {#each progress.recent_attempts as attempt}
            <li>
              <p><strong>{attempt.is_correct ? "Correct" : "Incorrect"}</strong> (D{attempt.difficulty})</p>
              <p>{attempt.prompt}</p>
              <p>Your answer: {attempt.user_answer}</p>
              <p>Expected: {attempt.corrected_answer}</p>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}

  {#if errorMessage}
    <p class="error">{errorMessage}</p>
  {/if}
</section>
