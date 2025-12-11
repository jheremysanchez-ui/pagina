import { Route, Navigate } from "react-router-dom";
import { connect } from "react-redux";

const PrivateRoute = ({
  element:  Element,
  auth: {isAuthentificated, loading},
  ...rest
 }) => (
  <Route
    {...rest}
    render={props => !isAuthentificated && !loading ? (
      <Navigate to= '/login'/>
    ):(
      <Element {...props}/>
    )}
  />
);  

const mapStateToProps = state => ({
  auth: state.root.Auth
})

export default connect(mapStateToProps, {})(PrivateRoute)