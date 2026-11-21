from app.extensions import db
from app.models.project import Project


def create_project(title, description, research_field, user_id):

    project = Project(
        title=title,
        description=description,
        research_field=research_field,
        user_id=user_id
    )

    db.session.add(project)
    db.session.commit()

    return project

def get_user_projects(user_id, status="ACTIVE"):
    projects = Project.query.filter_by( user_id=user_id, status=status ).all()
    return projects

def get_project_by_id(project_id, user_id):
    project = Project.query.filter_by(user_id = user_id , id = project_id).first()
    return project

def update_project(project,title=None,description=None,research_field=None,status=None):

    if title is not None:     # title = None means if user doesnt give title then keep None if not empty import that title
        project.title = title

    if description is not None:  # here only if user puts value it will not be None and if user wants to change then 
        project.description = description   #  the parameter will not be None so if cond will work if user doesnt change 
                                        # then the parameter will be None and here if condn will not work and same parametrs 
    if research_field is not None:      # will be present so we are updating this while changing only things requred for us
        project.research_field = research_field

    if status is not None:
        project.status = status

    db.session.commit()

    return project

def archive_project(project):
    project.status = "ARCHIVED"
    db.session.commit()
    return project

def delete_project(project):
    from app.services.paper_service import _remove_file
    for paper in project.papers:
        _remove_file(paper.file_path)
    db.session.delete(project)
    db.session.commit()

