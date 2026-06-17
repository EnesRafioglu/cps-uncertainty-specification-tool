const modelsContainer = document.querySelector("#models");
const relationsContainer = document.querySelector("#relations");

document.querySelector("#add-model").addEventListener("click", () => {
  addModel();
  updateNames();
});

document.querySelector("#add-relation").addEventListener("click", () => {
  addRelation();
  updateNames();
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

updateNames();
