const formData = new FormData();
const submitButton = document.querySelector(".send");
const mainImageFile = document.querySelector("input[name='mainImage']") ;
const imageFiles = document.querySelectorAll("input[name='images']") ;
const responseMessage = document.querySelector(".responseMessage") ;
const fieldList = ['title','description','price','texture','wash','place','note','story']
const variantList = ["color_code", "color_name", "sizes_s",  "sizes_m", "sizes_l"]

let bodyData = {}
function cleanFormDate() {
    formData.delete("image0")
    for (let i = 0 ;i < 4; i++) {
        if (imageFiles[i].files[0]){
            formData.delete(`image${i+1}`)
        } 
    }
}
document.addEventListener("submit",(e) => {
    e.preventDefault()
    // put form data into bodyDate for sending to background 
    for (let filed of fieldList){
        console.log(filed)
        bodyData[filed] = document.querySelector(`input[name='${filed}']`).value
    } 
    // put color variant into bodyDate for sending to background 
    bodyData["variants"] =[]
    for (let i = 0 ;i < 3; i++){
        let variant = {}
        for (let filed of variantList){
            console.log(document.querySelector(["input[name='color_name_1']"]).value)
            variant[filed] = document.querySelector([`input[name='${filed}_${i+1}']`]).value            
        }
    bodyData["variants"].push(variant)
    }
    bodyData["category"] = document.querySelector(".select").value
    // Put image file into FormDate for sending to /upload_image API 
    formData.append('image0',mainImageFile.files[0]);
    for (let i = 0 ;i < imageFiles.length; i++) {
        if (imageFiles[i].files[0]) {
            formData.append(`image${i+1}`, imageFiles[i].files[0])
        }
    }

    
    // Send FormDate to Python for uploading image into AWS S3 Server
    
    fetch("/upload_image",{
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.status === 413){
            responseMessage.innerText ="Files is too big ,only accept max : 16MB"
            cleanFormDate()
        }
        return response.json()
    })
    .then(imageJson => {
        //Get the image's url
        console.log(imageJson)
        if (imageJson['message']) {
            cleanFormDate()
            responseMessage.innerText = imageJson['message']
        } else {
            bodyData.images = imageJson
            console.log(bodyData.images)
            //Send whole data into background for storing  into SQL
            fetch("/store_data",{
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bodyData)
            })
            .then(response => {
                return response.json()
            })
            .then(json => {
                if (json['message'] === "Failed") {
                    cleanFormDate()
                    responseMessage.innerText = "Upload Failed! There is the same title in Database!"
                } else {
                    alert(json['message']);
                    cleanFormDate()
                    location.reload()
                }
            })
        }
    })
})


// const colorCount = document.querySelector(".colorCount")
// const colorForm = document.querySelector("#variant") ;
// colorForm.style.background ="red";
// const colorHTML = colorForm.cloneNode(true)
// colorCount.addEventListener("change",(e)=>{
//     console.log(colorHTML)
//     // e.target.value
//     colorForm.append(colorHTML)
// })
