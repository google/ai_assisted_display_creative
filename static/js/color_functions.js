function handleColorChange(colorPicker) {

    const color = colorPicker.toHEXString();

    var outerCircles = document.getElementsByClassName("outer-circle");
    var innerCircles = document.getElementsByClassName("inner-circle");

    for (var i=0;i<outerCircles.length;i++){

        outerCircles[i].setAttribute('stroke', color);
        innerCircles[i].setAttribute('stroke', color );
        innerCircles[i].setAttribute('fill', color );
    }
}

function handleSizeChange(e) {

    const {value, min, max} = e.target;

    var outerCircles = document.getElementsByClassName("outer-circle");
    var innerCircles = document.getElementsByClassName("inner-circle");
    var sizeSlider = document.getElementById("circle-size");
    const formerValue = parseInt(sizeSlider.getAttribute('former-value'));
    sizeSlider.setAttribute('former-value', value);

    const stepValue = 1;
    var steps = value - formerValue;

    var ratio = stepValue * Math.abs(steps);

    if (steps != 0){
        for (var i=0;i<outerCircles.length;i++){

            outR = parseInt(outerCircles[i].getAttribute('r'));
            inR = parseInt(innerCircles[i].getAttribute('r'));

            if (steps > 0){
                outerCircles[i].setAttribute('r', outR + ratio );
                innerCircles[i].setAttribute('r', inR + ratio );
            } else {
                outerCircles[i].setAttribute('r', Math.max(outR - ratio, 1) );
                innerCircles[i].setAttribute('r', Math.max(inR - ratio, 1) );
            }
        }
    }

}