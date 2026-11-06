(() => {
  const profileKeys = ['major', 'personal', 'academic', 'skill', 'transcriptText', 'resumeText'];
  const uploadDatabase = 'pathways-demo-uploads';
  const uploadStore = 'files';
  const page = window.location.pathname.split('/').pop();

  function showError(message) {
    let node = document.querySelector('[data-demo-error]');
    if (!node) {
      node = document.createElement('p');
      node.className = 'error';
      node.setAttribute('role', 'alert');
      node.dataset.demoError = '';
      (document.querySelector('main') || document.body).prepend(node);
    }
    node.textContent = message;
  }

  function openUploadDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(uploadDatabase, 1);
      request.onupgradeneeded = () => request.result.createObjectStore(uploadStore);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async function storeUpload(key, file) {
    const database = await openUploadDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(uploadStore, 'readwrite');
      transaction.objectStore(uploadStore).put(file, key);
      transaction.oncomplete = () => {
        database.close();
        resolve();
      };
      transaction.onerror = () => {
        database.close();
        reject(transaction.error);
      };
    });
  }

  async function readUpload(key) {
    const database = await openUploadDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(uploadStore, 'readonly');
      const request = transaction.objectStore(uploadStore).get(key);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
      transaction.oncomplete = () => database.close();
    });
  }

  async function removeUpload(key) {
    const database = await openUploadDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(uploadStore, 'readwrite');
      transaction.objectStore(uploadStore).delete(key);
      transaction.oncomplete = () => {
        database.close();
        resolve();
      };
      transaction.onerror = () => {
        database.close();
        reject(transaction.error);
      };
    });
  }

  async function clearUploads() {
    const database = await openUploadDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(uploadStore, 'readwrite');
      transaction.objectStore(uploadStore).clear();
      transaction.oncomplete = () => {
        database.close();
        resolve();
      };
      transaction.onerror = () => {
        database.close();
        reject(transaction.error);
      };
    });
  }

  function demoUrl(filename) {
    return `/demo/${filename.split('/').map(encodeURIComponent).join('/')}`;
  }

  function readProfile() {
    const profile = {};
    for (const key of profileKeys) {
      profile[key] = sessionStorage.getItem(`pathways.${key}`) || '';
    }
    return profile;
  }

  async function requestJson(path, options = {}) {
    const response = await fetch(path, { credentials: 'same-origin', ...options });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.error || 'The request could not be completed.');
    }
    return body;
  }

  async function submitAnalysis(form) {
    const fields = new FormData(form);
    for (const key of profileKeys) {
      const field = form.elements.namedItem(key);
      if (field && field.type !== 'file') {
        sessionStorage.setItem(`pathways.${key}`, field.value);
      }
    }

    const profile = readProfile();
    const body = new FormData();
    body.set('major', profile.major);
    body.set('interests', [profile.personal, profile.academic].filter(Boolean).join('\n'));
    body.set('goals', profile.academic);
    if (profile.skill) body.set('skills', profile.skill);
    body.set('transcript_text', profile.transcriptText);
    body.set('resume_text', profile.resumeText);

    const directTranscript = fields.get('transcript-file');
    const directResume = fields.get('resume-file');
    const transcript = directTranscript?.size
      ? directTranscript
      : await readUpload('transcript');
    const resume = directResume?.size
      ? directResume
      : await readUpload('resume');
    if (transcript) body.set('transcript', transcript, transcript.name || 'transcript.pdf');
    if (resume) body.set('resume', resume, resume.name || 'resume.pdf');

    const button = form.querySelector('button[type="submit"]');
    const originalText = button?.textContent;
    if (button) {
      button.disabled = true;
      button.textContent = 'Finding your pathways…';
    }
    try {
      const result = await requestJson('/api/analyze', { method: 'POST', body });
      sessionStorage.setItem('pathways.analysis', JSON.stringify(result));
      window.location.assign(demoUrl('recommendations.html'));
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Analysis failed. Please try again.');
      if (button) {
        button.disabled = false;
        button.textContent = originalText;
      }
    }
  }

  async function saveQuestionnaire(form) {
    for (const key of profileKeys) {
      const field = form.elements.namedItem(key);
      if (field) {
        sessionStorage.setItem(`pathways.${key}`, field.type === 'radio'
          ? form.querySelector(`[name="${key}"]:checked`)?.value || ''
          : field.value);
      }
    }
    for (const [inputName, key] of [['transcript-file', 'transcript'], ['resume-file', 'resume']]) {
      const input = form.elements.namedItem(inputName);
      if (input?.files?.[0]) {
        await storeUpload(key, input.files[0]);
        const status = input.closest('[data-drop]')?.querySelector('[data-file-status]');
        if (status) status.textContent = `Saved for analysis: ${input.files[0].name}`;
      }
    }
  }

  async function submitAccountForm(form) {
    const fields = Object.fromEntries(new FormData(form));
    const isSignup = Boolean(fields.name);
    const result = await requestJson(`/api/${isSignup ? 'signup' : 'login'}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fields),
    });
    sessionStorage.setItem('pathways.user', JSON.stringify(result.user));
    const next = form.dataset.next || '02-major 1.html';
    window.location.assign(demoUrl(isSignup ? next : (sessionStorage.getItem('pathways.major') ? '08-dashboard 1.html' : '02-major 1.html')));
  }

  async function runForm(form) {
    if (form.querySelector('[name="email"]') && form.querySelector('[name="password"]')) {
      await submitAccountForm(form);
      return;
    }
    if (form.dataset.next === '06-analysis 1.html') {
      await submitAnalysis(form);
      return;
    }
    await saveQuestionnaire(form);
    window.location.assign(demoUrl(form.dataset.next));
  }

  async function runAnalysisFromLink() {
    const form = document.createElement('form');
    await submitAnalysis(form);
  }

  function renderRecommendations() {
    const raw = sessionStorage.getItem('pathways.analysis');
    const result = raw ? JSON.parse(raw) : null;
    const roles = document.querySelector('.roles');
    const saveButton = document.querySelector('#save');
    if (!roles || !saveButton) return;
    if (!result?.suggested_pathway) {
      showError('No analysis is available yet. Complete your profile and submit it for recommendations.');
      return;
    }

    const pathways = [result.suggested_pathway, ...(result.alternative_pathways || [])];
    const summary = document.querySelector('main > .eyebrow');
    if (summary && result.student_summary) summary.textContent = result.student_summary;
    const heading = document.querySelector('main > h1');
    if (heading) heading.textContent = 'Your career pathways';
    const description = document.querySelector('main > h1 + p');
    if (description) description.textContent = 'Compare your matches and choose a next step to explore.';
    roles.replaceChildren();
    const title = document.querySelector('#selected-title');
    const fit = document.querySelector('#fit');
    const next = document.querySelector('#next');
    let selected = 0;
    let activeSaveButton = saveButton;
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem('pathways.savedPathway') || 'null');
    } catch {
      saved = null;
    }

    function updateDetails() {
      const pathway = pathways[selected];
      title.textContent = pathway.title;
      fit.textContent = pathway.why_fit;
      next.textContent = pathway.weekly_action;
      activeSaveButton.textContent = saved?.title === pathway.title ? 'Pathway saved' : 'Save pathway';
      activeSaveButton.setAttribute('aria-pressed', String(saved?.title === pathway.title));
    }

    pathways.forEach((pathway, index) => {
      const card = document.createElement('article');
      card.className = `role${index === 0 ? ' selected' : ''}`;
      const label = document.createElement('p');
      label.className = 'eyebrow';
      label.dataset.roleLabel = '';
      label.textContent = index === 0 ? 'Suggested pathway' : `Alternative ${index}`;
      const heading = document.createElement('h2');
      const button = document.createElement('button');
      button.className = 'role-button';
      button.type = 'button';
      button.textContent = pathway.title;
      button.setAttribute('aria-pressed', String(index === 0));
      heading.append(button);
      const score = document.createElement('p');
      score.className = 'muted';
      score.textContent = `Match score: ${pathway.match_score}%`;
      card.append(label, heading, score);
      button.addEventListener('click', () => {
        selected = index;
        for (const [position, item] of [...roles.children].entries()) {
          item.classList.toggle('selected', position === index);
          const itemButton = item.querySelector('button');
          itemButton.setAttribute('aria-pressed', String(position === index));
          item.querySelector('[data-role-label]').textContent = position === index
            ? 'Selected pathway'
            : `Alternative ${position}`;
        }
        updateDetails();
      });
      roles.append(card);
    });

    const save = saveButton.cloneNode(true);
    saveButton.replaceWith(save);
    activeSaveButton = save;
    save.addEventListener('click', async () => {
      const pathway = pathways[selected];
      try {
        await requestJson('/api/saved-pathway', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pathway }),
        });
        saved = pathway;
        localStorage.setItem('pathways.savedPathway', JSON.stringify(pathway));
        localStorage.setItem('pathways.savedRole', pathway.title);
        updateDetails();
      } catch (error) {
        showError(error instanceof Error ? error.message : 'Could not save this pathway.');
      }
    });
    updateDetails();

    document.querySelector('.note.muted')?.remove();
    const recommendations = [
      ['Skill gaps', result.skill_gaps],
      ['Recommended projects', result.recommended_projects],
      ['Recommended certifications', result.recommended_certifications],
      ['Internships', result.internships],
      ['Resources', result.resources],
    ].filter(([, items]) => Array.isArray(items) && items.length);
    if (recommendations.length) {
      const section = document.createElement('section');
      section.className = 'details';
      for (const [headingText, items] of recommendations) {
        const heading = document.createElement('h3');
        heading.textContent = headingText;
        const list = document.createElement('ul');
        for (const item of items) {
          const entry = document.createElement('li');
          entry.textContent = item;
          list.append(entry);
        }
        section.append(heading, list);
      }
      document.querySelector('main').append(section);
    }
  }

  function hydrateDashboard() {
    if (!document.querySelector('[data-summary="savedRole"]')) return;
    requestJson('/api/saved-pathway')
      .then(({ saved_pathway: pathway }) => {
        const node = document.querySelector('[data-summary="savedRole"]');
        node.textContent = pathway?.title || 'No saved pathway yet.';
      })
      .catch(error => showError(error instanceof Error ? error.message : 'Could not load your saved pathway.'));
  }

  async function initializeSession() {
    const { user } = await requestJson('/api/session');
    const publicPages = new Set([
      '00-welcome 2.html',
      '01-sign-in 1.html',
      '01-sign-up 1.html',
    ]);
    if (!user && !publicPages.has(decodeURIComponent(page))) {
      window.location.replace(demoUrl('01-sign-in 1.html'));
      return false;
    }
    if (user) {
      const navigation = document.querySelector('header nav');
      if (navigation && !navigation.querySelector('[data-demo-signout]')) {
        const button = document.createElement('button');
        button.className = 'btn secondary';
        button.dataset.demoSignout = '';
        button.textContent = 'Sign out';
        button.addEventListener('click', async () => {
          button.disabled = true;
          try {
            await requestJson('/api/logout', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
            sessionStorage.clear();
            localStorage.removeItem('pathways.savedRole');
            localStorage.removeItem('pathways.savedPathway');
            await clearUploads().catch(() => {
              showError('You are signed out, but selected files could not be cleared from this browser.');
            });
            window.location.assign(demoUrl('00-welcome 2.html'));
          } catch (error) {
            button.disabled = false;
            showError(error instanceof Error ? error.message : 'Could not sign out.');
          }
        });
        navigation.append(button);
      }
    }
    return true;
  }

  document.addEventListener('change', event => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || input.type !== 'file' || !input.files?.[0]) return;
    const key = input.name === 'transcript-file' ? 'transcript' : input.name === 'resume-file' ? 'resume' : null;
    if (key) {
      storeUpload(key, input.files[0])
        .then(() => {
          const status = input.closest('[data-drop]')?.querySelector('[data-file-status]');
          if (status) status.textContent = `Saved for analysis: ${input.files[0].name}`;
        })
        .catch(() => showError('Could not save the selected file. Please try another PDF.'));
    }
  });

  document.querySelectorAll('[data-drop]').forEach(drop => {
    const input = drop.querySelector('input[type="file"]');
    if (!input) return;
    drop.addEventListener('drop', event => {
      const file = event.dataTransfer?.files[0];
      if (!file) return;
      const transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  document.addEventListener('submit', event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.dataset.next) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    runForm(form).catch(error => {
      showError(error instanceof Error ? error.message : 'The request could not be completed.');
    });
  }, true);

  document.addEventListener('click', event => {
    const link = event.target instanceof Element ? event.target.closest('a') : null;
    if (!link) return;
    const target = decodeURIComponent(link.getAttribute('href') || '');
    if (link.textContent.trim() === 'Remove' && /transcript|resume/i.test(page)) {
      event.preventDefault();
      const key = /transcript/i.test(page) ? 'transcript' : 'resume';
      removeUpload(key).then(() => window.location.reload()).catch(() => showError('Could not remove the selected file.'));
    } else if (target.startsWith('06-analysis')) {
      event.preventDefault();
      const form = link.closest('form');
      Promise.resolve(form ? saveQuestionnaire(form) : undefined)
        .then(runAnalysisFromLink)
        .catch(error => showError(error instanceof Error ? error.message : 'Analysis failed.'));
    } else if (link.closest('form')) {
      event.preventDefault();
      saveQuestionnaire(link.closest('form'))
        .then(() => window.location.assign(demoUrl(target)))
        .catch(error => showError(error instanceof Error ? error.message : 'Could not save your profile.'));
    }
  }, true);

  for (const [inputName, key] of [['transcript-file', 'transcript'], ['resume-file', 'resume']]) {
    const input = document.querySelector(`[name="${inputName}"]`);
    const status = input?.closest('[data-drop]')?.querySelector('[data-file-status]');
    if (status) {
      readUpload(key).then(file => {
        if (file) status.textContent = `Saved for analysis: ${file.name}`;
      }).catch(() => showError('Could not read the selected file from this browser.'));
    }
  }
  initializeSession()
    .then(allowed => {
      if (!allowed) return;
      if (page === 'recommendations.html') renderRecommendations();
      hydrateDashboard();
    })
    .catch(error => showError(error instanceof Error ? error.message : 'Could not verify your account.'));
})();
