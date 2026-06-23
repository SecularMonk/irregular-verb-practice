<script lang="ts">
  import { onMount } from "svelte";
  import PracticePanel from "./components/PracticePanel.svelte";
  import ProgressPanel from "./components/ProgressPanel.svelte";
  import { ensureSession } from "./lib/api";

  let userId = "";
  let isBootstrapping = true;
  let bootstrapError = "";
  let progressRefreshToken = 0;
  let activeTab: "practice" | "progress" = "practice";

  onMount(async () => {
    try {
      userId = await ensureSession();
      progressRefreshToken += 1;
    } catch (error) {
      bootstrapError = error instanceof Error ? error.message : "Unable to start session.";
    } finally {
      isBootstrapping = false;
    }
  });

  function onAttemptSaved() {
    progressRefreshToken += 1;
  }

  function switchTab(tab: "practice" | "progress") {
    activeTab = tab;
  }
</script>

<main class="app-shell">
  <header>
    <h1>Irregular Verb Practice</h1>
    {#if userId}
      <p class="subtle">Anonymous session: {userId}</p>
    {/if}
  </header>

  {#if isBootstrapping}
    <p>Loading session...</p>
  {:else if bootstrapError}
    <p class="error">{bootstrapError}</p>
  {:else}
    <div class="tabs">
      <button
        class:tab-active={activeTab === "practice"}
        type="button"
        on:click={() => switchTab("practice")}
      >
        Practice
      </button>
      <button
        class:tab-active={activeTab === "progress"}
        type="button"
        on:click={() => switchTab("progress")}
      >
        Progress
      </button>
    </div>

    {#if activeTab === "practice"}
      <PracticePanel onAttemptSaved={onAttemptSaved} />
    {:else}
      <ProgressPanel refreshToken={progressRefreshToken} />
    {/if}
  {/if}
</main>
