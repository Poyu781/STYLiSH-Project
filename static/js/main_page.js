const logo = document.querySelector("#logo");
const men = document.querySelector("#men");
const women = document.querySelector("#women");
const accessory = document.querySelector("#acc");
const itemsSection = document.querySelector(".itemsSection");

function renderProduct(product, nodeDiv) {
    let node = document.createElement("div");
    node.classList.add("item");
    let img = product["main_image"];
    let title = product["title"];
    let price = product["price"];
    let colors = [];
    for (color of product["colors"]) {
        if (!(colors.includes(color["code"]))) {
            colors.push(color["code"]);
        }
    }
    console.log(1)
    console.log(colors)
    if (colors.length != 3) {
        colors.push("000000");
    }
    let htmlText = `
  <img src=${img}>
  <div class="information">
    <div class="productColors">
      <div class="color" style="background-color:#${colors[0]}"></div>
      <div class="color" style="background-color:#${colors[1]}"></div>
      <div class="color" style="background-color:#${colors[2]}"></div>          
    </div>
    <div class="productInfo">
      <div>${title}</div>
      <div>TWD:${price}</div>
    </div>
  </div>
  `;
    node.innerHTML = htmlText;
    nodeDiv.appendChild(node);
}

function main(url) {
    fetch(url)
        .then((response) => {
            return response.json();
        })
        .then((datalist) => {

            let dataArray = datalist["data"]; //I will get a list of dict

            let num = dataArray.length;

            for (let row = 0; row < num / 3; row++) {

                let node = document.createElement("div");
                node.classList.add("itemsWrap");
                node.setAttribute("id", `wrap${row}`);
                itemsSection.appendChild(node);
                itemsWrap = document.querySelector(`#wrap${row}`);
                for (let i = row * 3; i < (row + 1) * 3; i++) {

                    try {
                        renderProduct(dataArray[i], itemsWrap);
                    } catch {
                        let node = document.createElement("div");
                        node.classList.add("item");
                        itemsWrap.appendChild(node);
                    }
                }
            }
        });
}


women.addEventListener("click", () => {
    itemsSection.innerHTML ='';
    main("/api/1.0/products/women");
});

men.addEventListener("click", () => {
    itemsSection.innerHTML ='';
    main("/api/1.0/products/men");
});

accessory.addEventListener("click", () => {
    itemsSection.innerHTML ='';
    main("/api/1.0/products/accessories");
});

logo.addEventListener("click", () => {
    itemsSection.innerHTML ='';
    main("/api/1.0/products/all");
});

main("/api/1.0/products/all");
