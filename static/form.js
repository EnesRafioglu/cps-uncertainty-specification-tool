const modelsContainer = document.querySelector("#models");
const relationsContainer = document.querySelector("#relations");
const scenarioForm = document.querySelector("#scenario-form");
const validationOutput = document.querySelector("#validation-output");

document.querySelector("#add-model").addEventListener("click", () => {
  addModel();
  updateNames();
});

document.querySelector("#add-relation").addEventListener("click", () => {
  addRelation();
  updateNames();
});

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

  model.querySelector("[data-remove-model]").addEventListener("click", () => {
    model.remove();
    updateNames();
  });

  model.querySelector("[data-add-element]").addEventListener("click", () => {
    addElement(model);
    updateNames();
  });

  modelsContainer.appendChild(model);
}

function addElement(model) {
  const node = document.querySelector("#element-template").content.cloneNode(true);
  const element = node.querySelector("[data-element]");

  element.querySelector("[data-remove-element]").addEventListener("click", () => {
    element.remove();
    updateNames();
  });

  element.querySelector("[data-element-kind]").addEventListener("change", () => {
    updateElementVisibility(element);
  });
  element.querySelector("[data-uncertainty-type]").addEventListener("change", () => {
    updateElementVisibility(element);
  });

  model.querySelector("[data-elements]").appendChild(element);
  updateElementVisibility(element);
}

function addRelation() {
  const node = document.querySelector("#relation-template").content.cloneNode(true);
  const relation = node.querySelector("[data-relation]");

  relation.querySelector("[data-remove-relation]").addEventListener("click", () => {
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
    message.textContent = "No validation issues.";
    validationOutput.appendChild(message);
  }

  appendIssueList("Structural errors", result.structural_errors);
  appendIssueList("Completeness warnings", result.completeness_warnings);
  appendIssueList("Cross-field warnings", result.cross_field_warnings);

  if (result.valid) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Generate zonotopes";
    button.addEventListener("click", submitForGeneration);
    validationOutput.appendChild(button);
  } else {
    const message = document.createElement("p");
    message.textContent = "Generation is blocked until structural errors are fixed.";
    validationOutput.appendChild(message);
  }
}

function submitForGeneration() {
  scenarioForm.action = "/generate";
  scenarioForm.submit();
}

function appendIssueList(title, issues) {
  if (issues.length === 0) {
    return;
  }

  validationOutput.appendChild(createIssueList(title, issues));
}

function createIssueList(title, issues) {
  const section = document.createElement("section");
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
