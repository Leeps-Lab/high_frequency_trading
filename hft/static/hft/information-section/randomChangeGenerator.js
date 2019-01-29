randomChangeGenerator() {
    var luckyNumber = Math.floor(Math.random() * 3);
    let allTypes = ['bbo', 'mbo', 'ice'];
    let fieldName = allTypes[luckyNumber];

    let subFieldName = '';
    let newValue = 0;
    
    if (fieldName == 'bbo' || fieldName == 'mbo') {
      let allSides = ['bid', 'ask'];
      luckyNumber = Math.floor(Math.random() * 2);
      subFieldName = allSides[luckyNumber];
      newValue = Math.floor(Math.random() * 10);
    }
    if (fieldName == 'ice') {
      luckyNumber = Math.floor(Math.random() * 2);
      let allSides = ['inventory', 'cash', 'endowment'];
      subFieldName = allSides[luckyNumber];
      newValue = Math.floor(Math.random() * 10);
    }
    let result = [fieldName, subFieldName, newValue];
    console.log('random result', result)
    return result;
  }