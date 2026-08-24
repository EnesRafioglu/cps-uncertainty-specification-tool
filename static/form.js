const modelsContainer = document.querySelector("#models");
const relationsContainer = document.querySelector("#relations");
const scenarioForm = document.querySelector("#scenario-form");
const validationOutput = document.querySelector("#validation-output");

document.querySelector("#add-model").addEventListener("click", () => {
  clearValidationOutput();
  addModel();
  updateNames();
});

document.querySelector("#add-relation").addEventListener("click", () => {
  clearValidationOutput();
  addRelation();
  updateNames();
});

scenarioForm.addEventListener("input", handleFormEdit);
scenarioForm.addEventListener("change", handleFormEdit);

scenarioForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const response = await fetch("/api/validate", {
    method: "POST",
    body: new FormData(scenarioForm),
  });
  const data = await response.json();

  renderValidationResult(data.validation_result);
});

function addModel() {
  const node = document.querySelector("#model-template").content.cloneNode(true);
  const model = node.querySelector("[data-model]");

  setupToggleBlock(model);

  model.querySelector("[data-remove-model]").addEventListener("click", () => {
    clearValidationOutput();
    model.remove();
    updateNames();
  });

  model.querySelector("[data-add-element]").addEventListener("click", () => {
    clearValidationOutput();
    addElement(model);
    updateNames();
  });

  modelsContainer.appendChild(model);
}

function addElement(model) {
  const node = document.querySelector("#element-template").content.cloneNode(true);
  const element = node.querySelector("[data-element]");

  setupToggleBlock(element);

  element.querySelector("[data-remove-element]").addEventListener("click", () => {
    clearValidationOutput();
    element.remove();
    updateNames();
  });

  element.querySelector("[data-element-kind]").addEventListener("change", () => {
    updateElementVisibility(element);
  });
  element.querySelector("[data-uncertainty-type]").addEventListener("change", () => {
    updateElementVisibility(element);
  });
  element.querySelector("[data-atomic-component-type]").addEventListener("change", () => {
    updateClassificationVisibility(element);
  });
  element.querySelector("[data-location-type]").addEventListener("change", () => {
    updateClassificationVisibility(element);
  });

  model.querySelector("[data-elements]").appendChild(element);
  updateElementVisibility(element);
}

function addRelation() {
  const node = document.querySelector("#relation-template").content.cloneNode(true);
  const relation = node.querySelector("[data-relation]");

  setupToggleBlock(relation);

  relation.querySelector("[data-remove-relation]").addEventListener("click", () => {
    clearValidationOutput();
    relation.remove();
    updateNames();
  });

  relationsContainer.appendChild(relation);
}

function updateNames() {
  document.querySelectorAll("[data-model]").forEach((model, modelIndex) => {
    model.querySelectorAll("[data-name]").forEach((input) => {
      input.name = input.dataset.name.replaceAll("__model__", modelIndex);
    });

    model.querySelectorAll("[data-element]").forEach((element, elementIndex) => {
      element.querySelectorAll("[data-name]").forEach((input) => {
        input.name = input.dataset.name
          .replaceAll("__model__", modelIndex)
          .replaceAll("__element__", elementIndex);
      });
    });
  });

  document.querySelectorAll("[data-relation]").forEach((relation, relationIndex) => {
    relation.querySelectorAll("[data-name]").forEach((input) => {
      input.name = input.dataset.name.replaceAll("__relation__", relationIndex);
    });
  });

  updateElementReferenceOptions();
  updateBlockTitles();
}

function setupToggleBlock(block) {
  const button = block.querySelector("legend [data-toggle-block]");
  const body = block.querySelector("[data-block-body]");

  button.addEventListener("click", () => {
    body.hidden = !body.hidden;
    button.setAttribute("aria-expanded", String(!body.hidden));
    updateBlockTitles();
  });
}

function handleFormEdit() {
  clearValidationOutput();
  updateElementReferenceOptions();
  updateBlockTitles();
}

function updateElementReferenceOptions() {
  const elementIds = getElementIds();

  document.querySelectorAll("[data-element-reference]").forEach((select) => {
    const selectedValue = select.value;
    select.replaceChildren(createEmptyOption());

    elementIds.forEach((elementId) => {
      select.appendChild(new Option(elementId, elementId));
    });

    if (elementIds.includes(selectedValue)) {
      select.value = selectedValue;
    }
  });
}

function getElementIds() {
  const ids = [];

  document.querySelectorAll("[data-element]").forEach((element) => {
    const id = element.querySelector('input[name$=".id"]')?.value.trim();
    if (id && !ids.includes(id)) {
      ids.push(id);
    }
  });

  return ids;
}

function createEmptyOption() {
  return new Option("", "");
}

function updateBlockTitles() {
  document.querySelectorAll("[data-model]").forEach((model, modelIndex) => {
    const modelName = getValue(model, `scenario.models.${modelIndex}.name`);
    const modelId = getValue(model, `scenario.models.${modelIndex}.id`);
    setBlockTitle(model, `Model ${modelIndex + 1}${formatSummary(modelName || modelId)}`);

    model.querySelectorAll("[data-element]").forEach((element, elementIndex) => {
      const elementName = getValue(element, `scenario.models.${modelIndex}.elements.${elementIndex}.name`);
      const symbol = getValue(element, `scenario.models.${modelIndex}.elements.${elementIndex}.symbol`);
      const elementId = getValue(element, `scenario.models.${modelIndex}.elements.${elementIndex}.id`);
      setBlockTitle(element, `Element ${elementIndex + 1}${formatSummary(elementName || symbol || elementId)}`);
    });
  });

  document.querySelectorAll("[data-relation]").forEach((relation, relationIndex) => {
    const relationId = getValue(relation, `scenario.consistency_relations.${relationIndex}.id`);
    setBlockTitle(relation, `Consistency relation ${relationIndex + 1}${formatSummary(relationId)}`);
  });
}

function setBlockTitle(block, title) {
  const button = block.querySelector("legend [data-toggle-block]");
  const body = block.querySelector("[data-block-body]");
  const marker = body.hidden ? "> " : "v ";
  block.classList.toggle("is-collapsed", body.hidden);
  button.textContent = marker + title;
}

function getValue(container, name) {
  return container.querySelector(`[name="${name}"]`)?.value.trim() || "";
}

function formatSummary(value) {
  return value ? `: ${value}` : "";
}

function updateElementVisibility(element) {
  const kind = element.querySelector("[data-element-kind]").value;
  const uncertaintyType = element.querySelector("[data-uncertainty-type]").value;
  const isUncertain = kind === "uncertain";

  element.querySelector("[data-uncertainty-block]").hidden = !isUncertain;
  element.querySelector("[data-fixed-block]").hidden = isUncertain;
  element.querySelector("[data-classification-block]").hidden = !isUncertain;
  element.querySelector("[data-classification-block]").querySelectorAll("input, select, textarea").forEach((input) => {
    input.disabled = !isUncertain;
  });

  element.querySelectorAll("[data-uncertainty-input]").forEach((input) => {
    input.disabled = true;
  });
  element.querySelector("[data-uncertainty-type]").disabled = !isUncertain;
  element.querySelectorAll("[data-fixed-input]").forEach((input) => {
    input.disabled = isUncertain;
  });

  if (isUncertain) {
    element.querySelectorAll("[data-uncertainty-input]").forEach((input) => {
      input.disabled = false;
    });
    element.querySelectorAll("[data-uncertainty-fields]").forEach((fieldBlock) => {
      const active = fieldBlock.dataset.uncertaintyFields === uncertaintyType;
      fieldBlock.hidden = !active;
      fieldBlock.querySelectorAll("input, select, textarea").forEach((input) => {
        input.disabled = !active;
      });
    });
  }

  updateClassificationVisibility(element);
}

function updateClassificationVisibility(element) {
  const classificationBlock = element.querySelector("[data-classification-block]");
  const atomicComponentType = element.querySelector("[data-atomic-component-type]").value;
  const locationType = element.querySelector("[data-location-type]").value;

  element.querySelectorAll("[data-atomic-subtype]").forEach((fieldBlock) => {
    const active = !classificationBlock.hidden && fieldBlock.dataset.atomicSubtype === atomicComponentType;
    fieldBlock.hidden = !active;
    fieldBlock.querySelectorAll("input, select, textarea").forEach((input) => {
      input.disabled = !active;
    });
  });

  element.querySelectorAll("[data-location-subtype]").forEach((fieldBlock) => {
    const active = !classificationBlock.hidden && fieldBlock.dataset.locationSubtype === locationType;
    fieldBlock.hidden = !active;
    fieldBlock.querySelectorAll("input, select, textarea").forEach((input) => {
      input.disabled = !active;
    });
  });
}

function renderValidationResult(result) {
  validationOutput.hidden = false;
  validationOutput.innerHTML = "";

  validationOutput.appendChild(createHeading("Validation output", 2));
  if (
    result.structural_errors.length === 0
    && result.completeness_warnings.length === 0
    && result.cross_field_warnings.length === 0
  ) {
    const message = document.createElement("p");
    message.className = "validation-message validation-message-success";
    message.textContent = "No validation issues.";
    validationOutput.appendChild(message);
  }

  appendIssueList("Structural errors", result.structural_errors, "structural");
  appendIssueList("Completeness warnings", result.completeness_warnings, "completeness");
  appendIssueList("Cross-field warnings", result.cross_field_warnings, "cross-field");

  if (result.valid) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Generate zonotopes";
    button.addEventListener("click", submitForGeneration);
    validationOutput.appendChild(button);
  } else {
    const message = document.createElement("p");
    message.className = "validation-message validation-message-blocked";
    message.textContent = "Generation is blocked until structural errors are fixed.";
    validationOutput.appendChild(message);
  }
}

function clearValidationOutput() {
  validationOutput.hidden = true;
  validationOutput.innerHTML = "";
}

function submitForGeneration() {
  scenarioForm.action = "/generate";
  scenarioForm.submit();
}

function appendIssueList(title, issues, kind) {
  if (issues.length === 0) {
    return;
  }

  validationOutput.appendChild(createIssueList(title, issues, kind));
}

function createIssueList(title, issues, kind) {
  const section = document.createElement("section");
  section.className = `validation-card validation-card-${kind}`;
  section.appendChild(createHeading(title, 3));

  const list = document.createElement("ul");
  issues.forEach((issue) => {
    const item = document.createElement("li");
    item.textContent = issue;
    list.appendChild(item);
  });

  section.appendChild(list);
  return section;
}

function createHeading(text, level) {
  const heading = document.createElement(`h${level}`);
  heading.textContent = text;
  return heading;
}

updateNames();
