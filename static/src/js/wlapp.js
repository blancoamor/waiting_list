var app = angular.module('wlApp', []);


app.controller('wlCtrl',function($scope, $http,$interval) {
    $scope.dni= "";
    $scope.telefono= "";
    $scope.area_ids= [];

    $scope.step= 1;
    $scope.numero = '';

    $scope.markMe = function(id){
       $scope.area_ids.push(id);
        if ($scope.active){
           $scope.active = false;

        } else {
           $scope.active = true;
        }
        $scope.step++;
    }


    $scope.sendData = function() {
        $scope.step++;
               
        $http.post("/wl/x/1/send", {
            params : {
                dni:$scope.dni,
                telefono:$scope.telefono,
                area_ids : $scope.area_ids
                
            }
        }).success(function (data, status, headers, config) {
                $scope.step++;
                $scope.numero = data.result.name
                $scope.meeting_point = data.result.meeting_point
                restart = $interval(function(){

                    $scope.dni= "";
                    $scope.telefono= "";
                    $scope.area_ids= [];

                    $scope.step= 1;
                    $scope.numero = '';
                    $interval.cancel(restart);

                },5000);
        }).error(function (data, status, headers, config) {
                console.log(data)
        });


}

});