import {Express} from "express";
import {IMicroServiceApp} from "@cataloger/core/interfaces/microserviceapp.interface";
// import routes
// import services
// Lazy Begin Imports
import {{ "{" }}{{cookiecutter.project_camel_case}}Conn{{ "}" }} from "./connections/{{cookiecutter.project_kebab}}.conn";
// Lazy End Imports

export class {{cookiecutter.project_camel_case}}MicroServiceApp implements IMicroServiceApp {

    getSyncProcess(): any[] {

        // register connections of the microservice
        // new MigrationService().registerConnection('placeholder', placeholderConn);

        // array of promises to be completed before run the application
        return [
            // Lazy Begin Promises
            {{cookiecutter.project_camel_case}}Conn,
            // Lazy End Promises
        ]
    }

    setRoutes(app: Express): void {
        // app.use('/<placeholder>', PlaceholderRoutes);
    }

    getAdminBroResources(): any[] {
        return [
            // Lazy Begin Bro
            // Lazy End Bro
        ]
    }

}
